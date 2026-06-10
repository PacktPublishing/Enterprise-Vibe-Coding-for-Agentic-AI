"""
AI Marketing Agent Pipeline Portal

A Flask web app that orchestrates specialised AI agents in a pipeline
to generate comprehensive marketing campaigns.

Usage:
    python app.py
    Open http://127.0.0.1:5000 in your browser
"""

import asyncio
import io
import json
import os
import time
import uuid
from datetime import datetime

import requests as http_requests          # for Microsoft Graph calls
from flask import Flask, Response, render_template, request, jsonify, send_file
from fpdf import FPDF

# ---------------------------------------------------------------------------
# Agents package — all agents, clients, and helpers are created at import
# ---------------------------------------------------------------------------
from agents import (
    # Configuration
    DEPLOYMENT_NAME,
    IMAGES_DIR,
    # Credentials & clients
    credential,
    # Async event loop
    _loop,
    # Helpers
    generate_campaign_image as _generate_campaign_image,
    parse_agent_json as _parse_agent_json,
    # Pipeline agents
    strategy_agent,
    content_agent,
    audience_agent,
    performance_agent,
    # Channel agents
    email_agent,
    instagram_agent,
    tiktok_agent,
    linkedin_agent,
    # Look-up dicts
    MAIN_AGENTS,
    CHANNEL_AGENTS,
    IMAGE_CHANNELS,
)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generated_images/<filename>")
def serve_generated_image(filename):
    """Serve a generated campaign image."""
    return send_file(os.path.join(IMAGES_DIR, filename), mimetype="image/png")


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


@app.route("/generate", methods=["POST"])
def generate_campaign():
    """SSE endpoint — runs the 4-agent pipeline and streams progress."""
    data = request.get_json()
    product_name = data.get("product_name", "").strip()
    product_description = data.get("product_description", "").strip()
    target_region = data.get("target_region", "North America")
    budget = data.get("budget", "100000")

    if not product_name:
        return Response(
            "data: " + json.dumps({"type": "error", "text": "Product name is required"}) + "\n\n",
            content_type="text/event-stream",
        )

    brief = (
        f"Product: {product_name}\n"
        f"Description: {product_description}\n"
        f"Target Region: {target_region}\n"
        f"Marketing Budget: ${budget}"
    )

    def generate():
        results = {}

        # --- Log: Campaign brief received ---
        yield "data: " + json.dumps({
            "type": "log",
            "time": _timestamp(),
            "text": f"Campaign brief received: {product_name}",
            "color": "default",
        }) + "\n\n"

        yield "data: " + json.dumps({
            "type": "log",
            "time": _timestamp(),
            "text": f"Target region: {target_region} | Budget: ${budget}",
            "color": "info",
        }) + "\n\n"

        # ===================================================================
        # 1. Strategy Agent
        # ===================================================================
        yield "data: " + json.dumps({
            "type": "agent_start",
            "agent": "strategy",
            "time": _timestamp(),
        }) + "\n\n"

        yield "data: " + json.dumps({
            "type": "log",
            "time": _timestamp(),
            "text": "Strategy Agent activated - analyzing market positioning...",
            "color": "strategy",
        }) + "\n\n"

        try:
            strategy_prompt = (
                f"Create a marketing strategy for this campaign:\n\n{brief}\n\n"
                "CRITICAL: Before answering, you MUST use your web_search tool to look up:\n"
                "  1. Current market trends and statistics for this product category in the target region\n"
                "  2. Competitor campaigns or similar products in this space\n"
                "  3. Regional consumer behaviour and demographics\n"
                "Do NOT skip the web search. Use it now, then produce your JSON output based on the real data you find.\n"
                "Return ONLY valid JSON."
            )

            # Run strategy agent and inspect full response for tool usage
            async def _run_strategy():
                response = await strategy_agent.run(
                    strategy_prompt,
                    options={"tool_choice": "required", "allow_multiple_tool_calls": True},
                )
                return response

            future = asyncio.run_coroutine_threadsafe(_run_strategy(), _loop)
            response = future.result(timeout=120)

            # Debug: dump full response structure to terminal
            print(f"  [strategy] Response type: {type(response).__name__}")
            print(f"  [strategy] Response text (first 300): {str(response)[:300]}")
            try:
                resp_dict = response.to_dict()
                print(f"  [strategy] Response dict keys: {list(resp_dict.keys())}")
                if 'messages' in resp_dict:
                    for i, msg in enumerate(resp_dict['messages']):
                        print(f"  [strategy] Message {i}: role={msg.get('role')}, contents_count={len(msg.get('contents', []))}")
                        for j, c in enumerate(msg.get('contents', [])):
                            ctype = c.get('type', 'unknown')
                            print(f"    Content {j}: type={ctype}")
                            if ctype == 'function_call':
                                print(f"      function_name={c.get('function_name')}")
                            if 'annotations' in c:
                                for a in c['annotations']:
                                    print(f"      annotation: tool_name={a.get('tool_name')}, url={a.get('url', '')[:80]}")
            except Exception as dbg_err:
                print(f"  [strategy] Debug dump error: {dbg_err}")

            raw = str(response)

            # Detect tool usage from response messages
            tool_names_seen = set()
            web_search_urls = []
            try:
                resp_dict = response.to_dict()
                for msg in resp_dict.get('messages', []):
                    for c in msg.get('contents', []):
                        ctype = c.get('type', '')
                        if ctype == 'function_call' or 'function' in ctype:
                            tool_names_seen.add(c.get('function_name', c.get('name', 'tool')))
                        if 'annotations' in c:
                            for ann in c['annotations']:
                                tn = ann.get('tool_name')
                                url = ann.get('url', '')
                                if tn:
                                    tool_names_seen.add(tn)
                                # URL in annotation = web search was used
                                if url:
                                    tool_names_seen.add('web_search')
                                    web_search_urls.append(url)
            except Exception:
                pass

            # Emit log entries for each tool detected
            if tool_names_seen:
                for tn in sorted(tool_names_seen):
                    yield "data: " + json.dumps({
                        "type": "log",
                        "time": _timestamp(),
                        "text": f"Strategy Agent used tool: {tn}",
                        "color": "tool",
                    }) + "\n\n"
                # Log the sources found
                for url in web_search_urls[:5]:
                    # Extract domain for cleaner display
                    domain = url.split("//")[-1].split("/")[0] if "//" in url else url[:60]
                    yield "data: " + json.dumps({
                        "type": "log",
                        "time": _timestamp(),
                        "text": f"  Source: {domain}",
                        "color": "tool",
                    }) + "\n\n"
            else:
                yield "data: " + json.dumps({
                    "type": "log",
                    "time": _timestamp(),
                    "text": "Strategy Agent did not invoke any tools",
                    "color": "info",
                }) + "\n\n"

            strategy_data = _parse_agent_json(str(raw), "strategy")
            results["strategy"] = strategy_data

            yield "data: " + json.dumps({
                "type": "agent_complete",
                "agent": "strategy",
                "data": strategy_data,
                "time": _timestamp(),
            }) + "\n\n"

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": "Strategy Agent completed - KPIs and timeline defined",
                "color": "default",
            }) + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({
                "type": "agent_error",
                "agent": "strategy",
                "error": str(e),
            }) + "\n\n"
            yield "data: " + json.dumps({"type": "done"}) + "\n\n"
            return

        # ===================================================================
        # 2. Content Agent
        # ===================================================================
        yield "data: " + json.dumps({
            "type": "agent_start",
            "agent": "content",
            "time": _timestamp(),
        }) + "\n\n"

        yield "data: " + json.dumps({
            "type": "log",
            "time": _timestamp(),
            "text": "Content Agent activated - generating campaign messaging...",
            "color": "content",
        }) + "\n\n"

        try:
            content_prompt = (
                f"Create campaign messaging for this product:\n\n{brief}\n\n"
                f"Strategic context: {json.dumps(strategy_data)}\n\n"
                "Return ONLY valid JSON."
            )
            future = asyncio.run_coroutine_threadsafe(
                content_agent.run(content_prompt), _loop
            )
            raw = future.result(timeout=60)
            content_data = _parse_agent_json(str(raw), "content")
            results["content"] = content_data

            yield "data: " + json.dumps({
                "type": "agent_complete",
                "agent": "content",
                "data": content_data,
                "time": _timestamp(),
            }) + "\n\n"

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": "Content Agent completed - headlines and taglines created",
                "color": "default",
            }) + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({
                "type": "agent_error",
                "agent": "content",
                "error": str(e),
            }) + "\n\n"
            yield "data: " + json.dumps({"type": "done"}) + "\n\n"
            return

        # ===================================================================
        # 3. Visual Generation Step (gpt-image-1.5)
        # ===================================================================
        yield "data: " + json.dumps({
            "type": "agent_start",
            "agent": "visual",
            "time": _timestamp(),
        }) + "\n\n"

        yield "data: " + json.dumps({
            "type": "log",
            "time": _timestamp(),
            "text": "Visual Generation activated - creating campaign images...",
            "color": "visual",
        }) + "\n\n"

        try:
            headline = content_data.get("primary_headline", product_name)
            taglines = content_data.get("taglines", [])
            tone = content_data.get("tone", "modern and professional")

            hero_prompt = (
                f"Create a professional marketing hero banner image for a campaign called \"{headline}\". "
                f"Product: {product_name} — {product_description}. "
                f"Visual style: {tone}. "
                "The image should be visually striking, modern, and suitable for a digital campaign landing page. "
                "Do NOT include any text, letters, or words in the image."
            )

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": "Generating campaign image...",
                "color": "visual",
            }) + "\n\n"

            hero_bytes = _generate_campaign_image(hero_prompt, size="1024x1024")
            hero_filename = f"hero_{uuid.uuid4().hex[:8]}.png"
            hero_path = os.path.join(IMAGES_DIR, hero_filename)
            with open(hero_path, "wb") as f:
                f.write(hero_bytes)

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": f"Campaign image generated ({len(hero_bytes)//1024} KB)",
                "color": "visual",
            }) + "\n\n"

            visual_data = {
                "hero_image_url": f"/generated_images/{hero_filename}",
                "hero_prompt": hero_prompt,
            }
            results["visual"] = visual_data

            yield "data: " + json.dumps({
                "type": "agent_complete",
                "agent": "visual",
                "data": visual_data,
                "time": _timestamp(),
            }) + "\n\n"

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": "Visual Generation completed - campaign image created",
                "color": "default",
            }) + "\n\n"

        except Exception as e:
            print(f"  [visual] Image generation error: {e}")
            yield "data: " + json.dumps({
                "type": "agent_error",
                "agent": "visual",
                "error": str(e),
            }) + "\n\n"
            # Visual is non-critical, continue pipeline
            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": f"Visual generation failed ({e}) - continuing pipeline...",
                "color": "default",
            }) + "\n\n"

        # ===================================================================
        # 4. Audience Agent
        # ===================================================================
        yield "data: " + json.dumps({
            "type": "agent_start",
            "agent": "audience",
            "time": _timestamp(),
        }) + "\n\n"

        yield "data: " + json.dumps({
            "type": "log",
            "time": _timestamp(),
            "text": "Audience Agent activated - segmenting target demographics...",
            "color": "audience",
        }) + "\n\n"

        try:
            audience_prompt = (
                f"Define target audience segments for this campaign:\n\n{brief}\n\n"
                f"Strategic context: {json.dumps(strategy_data)}\n\n"
                "Return ONLY valid JSON."
            )
            future = asyncio.run_coroutine_threadsafe(
                audience_agent.run(audience_prompt), _loop
            )
            raw = future.result(timeout=60)
            audience_data = _parse_agent_json(str(raw), "audience")
            results["audience"] = audience_data

            yield "data: " + json.dumps({
                "type": "agent_complete",
                "agent": "audience",
                "data": audience_data,
                "time": _timestamp(),
            }) + "\n\n"

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": "Audience Agent completed - segments identified and sized",
                "color": "default",
            }) + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({
                "type": "agent_error",
                "agent": "audience",
                "error": str(e),
            }) + "\n\n"
            yield "data: " + json.dumps({"type": "done"}) + "\n\n"
            return

        # ===================================================================
        # 5. Performance Agent
        # ===================================================================
        yield "data: " + json.dumps({
            "type": "agent_start",
            "agent": "performance",
            "time": _timestamp(),
        }) + "\n\n"

        yield "data: " + json.dumps({
            "type": "log",
            "time": _timestamp(),
            "text": "Performance Agent activated - projecting ROI and metrics...",
            "color": "performance",
        }) + "\n\n"

        try:
            performance_prompt = (
                f"Project performance metrics and ROI for this campaign:\n\n{brief}\n\n"
                f"Strategy: {json.dumps(strategy_data)}\n"
                f"Audience: {json.dumps(audience_data)}\n\n"
                "Return ONLY valid JSON."
            )
            future = asyncio.run_coroutine_threadsafe(
                performance_agent.run(performance_prompt), _loop
            )
            raw = future.result(timeout=60)
            performance_data = _parse_agent_json(str(raw), "performance")
            results["performance"] = performance_data

            yield "data: " + json.dumps({
                "type": "agent_complete",
                "agent": "performance",
                "data": performance_data,
                "time": _timestamp(),
            }) + "\n\n"

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": "Performance Agent completed - conversion estimates ready",
                "color": "default",
            }) + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({
                "type": "agent_error",
                "agent": "performance",
                "error": str(e),
            }) + "\n\n"

        # --- Done ---
        yield "data: " + json.dumps({"type": "done", "results": results}) + "\n\n"

    return Response(generate(), content_type="text/event-stream")


@app.route("/export", methods=["POST"])
def export_report():
    """Generate a polished, agency-quality PDF report from campaign results."""
    data = request.get_json() or {}

    # --- Helpers ----------------------------------------------------------
    def safe(text):
        if not text:
            return ""
        return str(text).encode("latin-1", errors="replace").decode("latin-1")

    # Brand colours
    PURPLE    = (69, 39, 160)
    TEAL      = (0, 191, 165)
    DARK      = (30, 30, 30)
    MID       = (80, 80, 80)
    LIGHT     = (130, 130, 130)
    WHITE     = (255, 255, 255)
    BG_LIGHT  = (245, 243, 255)   # light purple tint
    BG_TEAL   = (232, 252, 248)   # light teal tint
    LINE_GRAY = (210, 210, 210)

    PAGE_W = 210   # A4 width mm
    MARGIN = 15
    CONTENT_W = PAGE_W - 2 * MARGIN

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.set_left_margin(MARGIN)
    pdf.set_right_margin(MARGIN)

    # =====================================================================
    # COVER PAGE
    # =====================================================================
    pdf.add_page()

    # Purple header band
    pdf.set_fill_color(*PURPLE)
    pdf.rect(0, 0, PAGE_W, 90, style="F")

    # White title text on purple
    pdf.set_y(22)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*WHITE)
    pdf.cell(CONTENT_W, 14, safe("AI Marketing Campaign"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 16)
    pdf.cell(CONTENT_W, 10, safe("Strategic Report"), new_x="LMARGIN", new_y="NEXT", align="C")

    # Product name & date below the band
    product_name = safe(data.get("brief", {}).get("product_name", ""))
    if not product_name:
        # try to derive from content headline
        product_name = safe(data.get("content", {}).get("primary_headline", "Campaign"))
    pdf.set_y(100)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(CONTENT_W, 10, product_name, align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*LIGHT)
    pdf.cell(CONTENT_W, 8, safe(f"Generated {datetime.now().strftime('%B %d, %Y')}"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)
    region = safe(data.get("brief", {}).get("target_region", ""))
    budget = safe(data.get("brief", {}).get("budget", ""))
    if region or budget:
        meta_parts = []
        if region:
            meta_parts.append(f"Region: {region}")
        if budget:
            meta_parts.append(f"Budget: ${budget}")
        pdf.cell(CONTENT_W, 7, safe("  |  ".join(meta_parts)), new_x="LMARGIN", new_y="NEXT", align="C")

    # Teal accent line
    pdf.ln(10)
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.8)
    mid = PAGE_W / 2
    pdf.line(mid - 30, pdf.get_y(), mid + 30, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(8)

    # Executive summary snippet
    strat_overview = safe(data.get("strategy", {}).get("strategic_overview", ""))
    if strat_overview:
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(*MID)
        # Truncate for cover
        snippet = strat_overview[:400] + ("..." if len(strat_overview) > 400 else "")
        pdf.multi_cell(CONTENT_W, 6, snippet, align="C")

    # --- Reusable drawing helpers ----------------------------------------
    def ensure_space(needed_mm):
        """Add a new page if less than needed_mm remain."""
        if pdf.get_y() + needed_mm > pdf.h - 25:
            pdf.add_page()

    def section_title(title):
        ensure_space(20)
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*PURPLE)
        pdf.cell(CONTENT_W, 10, safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*PURPLE)
        pdf.set_line_width(0.6)
        pdf.line(MARGIN, pdf.get_y(), MARGIN + CONTENT_W, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(5)

    def sub_label(text):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*MID)
        pdf.cell(CONTENT_W, 7, safe(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def body_text(text):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(CONTENT_W, 5.5, safe(text))
        pdf.ln(2)

    def draw_kpi_row(name, value, desc=""):
        ensure_space(16)
        y_start = pdf.get_y()
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK)
        pdf.cell(110, 7, safe(name))
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*PURPLE)
        pdf.cell(CONTENT_W - 110, 7, safe(value), new_x="LMARGIN", new_y="NEXT")
        if desc:
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*LIGHT)
            pdf.multi_cell(CONTENT_W, 4.5, safe(desc))
        # Subtle separator
        pdf.set_draw_color(*LINE_GRAY)
        pdf.line(MARGIN, pdf.get_y() + 1.5, MARGIN + CONTENT_W, pdf.get_y() + 1.5)
        pdf.ln(4)

    def draw_stat_box(label_text, value_text, color, x, y, w=55, h=28):
        """Draw a coloured stat card that wraps long text."""
        pad = 4
        inner_w = w - 2 * pad
        # Measure the value text height so the box can grow
        pdf.set_font("Helvetica", "B", 11)
        lines_needed = pdf.multi_cell(inner_w, 5.5, safe(value_text), dry_run=True, output="LINES")
        val_h = max(len(lines_needed) * 5.5, 8)
        actual_h = max(h, 8 + val_h + 2 * pad + 4)

        pdf.set_draw_color(*color)
        pdf.set_line_width(0.4)
        pdf.rect(x, y, w, actual_h, style="D")

        # Label
        pdf.set_xy(x + pad, y + pad)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*LIGHT)
        pdf.cell(inner_w, 5, safe(label_text), align="C", new_x="LMARGIN", new_y="NEXT")

        # Value (wraps)
        pdf.set_xy(x + pad, y + pad + 8)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*color)
        pdf.multi_cell(inner_w, 5.5, safe(value_text), align="C")
        pdf.set_line_width(0.2)

        return actual_h  # so caller can position after the box

    # =====================================================================
    # 1. STRATEGY
    # =====================================================================
    strategy = data.get("strategy", {})
    if strategy:
        pdf.add_page()
        section_title("Strategy & Market Analysis")

        if strategy.get("strategic_overview"):
            sub_label("Strategic Overview")
            body_text(strategy["strategic_overview"])

        kpis = strategy.get("kpis", [])
        if kpis:
            pdf.ln(2)
            sub_label("Key Performance Indicators")
            pdf.ln(1)
            for kpi in kpis:
                draw_kpi_row(
                    kpi.get("name", ""),
                    kpi.get("target", ""),
                    kpi.get("description", ""),
                )

        if strategy.get("timeline"):
            ensure_space(20)
            pdf.ln(3)
            # Timeline in a tinted box
            pdf.set_fill_color(*BG_LIGHT)
            y0 = pdf.get_y()
            pdf.set_x(MARGIN)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*PURPLE)
            pdf.cell(CONTENT_W, 7, safe("Timeline"), new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*DARK)
            pdf.set_x(MARGIN)
            pdf.multi_cell(CONTENT_W, 5.5, safe(strategy["timeline"]), fill=True)
            pdf.ln(1)

    # =====================================================================
    # 2. CONTENT
    # =====================================================================
    content = data.get("content", {})
    if content:
        pdf.add_page()
        section_title("Creative Content")

        headline = content.get("primary_headline", "")
        if headline:
            ensure_space(20)
            # Big headline in tinted box
            pdf.set_fill_color(*BG_LIGHT)
            pdf.set_x(MARGIN)
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(*PURPLE)
            pdf.multi_cell(CONTENT_W, 10, safe(headline), align="C", fill=True)
            pdf.ln(4)

        taglines = content.get("taglines", [])
        if taglines:
            sub_label("Taglines")
            for t in taglines:
                ensure_space(8)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(*DARK)
                pdf.cell(6, 6, safe("\x95"))  # bullet
                pdf.multi_cell(CONTENT_W - 6, 6, safe(t))
                pdf.ln(1)
            pdf.ln(2)

        messages = content.get("campaign_messages", [])
        if messages:
            sub_label("Campaign Messages")
            for i, m in enumerate(messages, 1):
                ensure_space(12)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*PURPLE)
                pdf.cell(8, 6, safe(f"{i}."))
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(*DARK)
                pdf.multi_cell(CONTENT_W - 8, 5.5, safe(m))
                pdf.ln(2)

        if content.get("tone"):
            ensure_space(14)
            pdf.ln(2)
            sub_label("Tone & Voice")
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(*MID)
            pdf.multi_cell(CONTENT_W, 5.5, safe(content["tone"]))

    # =====================================================================
    # 3. CAMPAIGN VISUALS
    # =====================================================================
    visual = data.get("visual", {})
    if visual:
        hero_url = visual.get("hero_image_url", "")
        if hero_url:
            fname = hero_url.rsplit("/", 1)[-1] if "/" in hero_url else hero_url
            img_path = os.path.join(IMAGES_DIR, fname)
            if os.path.isfile(img_path):
                pdf.add_page()
                section_title("Campaign Visual")
                ensure_space(150)
                try:
                    # Centre the image
                    img_w = 160
                    img_x = (PAGE_W - img_w) / 2
                    pdf.image(img_path, x=img_x, w=img_w)
                    pdf.ln(6)
                except Exception as img_err:
                    print(f"  [export] Failed to embed image: {img_err}")
                    body_text(f"[Image could not be embedded: {img_err}]")

                if visual.get("hero_prompt"):
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(*LIGHT)
                    pdf.multi_cell(CONTENT_W, 4, safe(f"Prompt: {visual['hero_prompt']}"), align="C")

    # =====================================================================
    # 4. AUDIENCE SEGMENTS
    # =====================================================================
    audience = data.get("audience", {})
    if audience:
        pdf.add_page()
        section_title("Audience Segmentation")

        segments = audience.get("segments", [])
        for seg in segments:
            ensure_space(28)
            seg_name = seg.get("name", "")
            seg_reach = seg.get("potential_reach", "")
            tags = seg.get("tags", [])

            # Segment name row with teal reach badge
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*DARK)
            pdf.cell(100, 7, safe(seg_name))
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*TEAL)
            pdf.cell(CONTENT_W - 100, 7, safe(seg_reach), align="R", new_x="LMARGIN", new_y="NEXT")

            if tags:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*LIGHT)
                pdf.multi_cell(CONTENT_W, 5, safe(", ".join(tags)))

            # Separator
            pdf.set_draw_color(*LINE_GRAY)
            pdf.line(MARGIN, pdf.get_y() + 2, MARGIN + CONTENT_W, pdf.get_y() + 2)
            pdf.ln(6)

        if audience.get("total_reach"):
            ensure_space(22)
            pdf.ln(2)
            pdf.set_fill_color(*BG_TEAL)
            pdf.set_x(MARGIN)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*TEAL)
            pdf.multi_cell(CONTENT_W, 8, safe(f"Total Addressable Reach: {audience['total_reach']}"),
                           align="C", fill=True)

    # =====================================================================
    # 5. PERFORMANCE PROJECTIONS
    # =====================================================================
    performance = data.get("performance", {})
    if performance:
        pdf.add_page()
        section_title("Performance Projections")

        # Stat boxes for conversion & ROI
        conv = performance.get("conversion_rate", "")
        roi = performance.get("estimated_roi", "")
        if conv or roi:
            ensure_space(50)
            box_y = pdf.get_y() + 2
            box_w = (CONTENT_W - 10) / 2

            h1 = 30
            h2 = 30
            if conv:
                h1 = draw_stat_box("Conversion Rate", conv, TEAL, MARGIN, box_y, w=box_w, h=30)
            if roi:
                h2 = draw_stat_box("Estimated ROI", roi, PURPLE, MARGIN + box_w + 10, box_y, w=box_w, h=30)

            pdf.set_y(box_y + max(h1, h2) + 6)

        metrics = performance.get("metrics", [])
        if metrics:
            sub_label("Performance Metrics")
            pdf.ln(1)
            for m in metrics:
                draw_kpi_row(
                    m.get("name", ""),
                    m.get("value", ""),
                    m.get("description", ""),
                )

    # =====================================================================
    # 6. CHANNEL DISTRIBUTION (if available)
    # =====================================================================
    channels_data = data.get("channels", {})
    channel_names = {"email": "Email Campaign", "instagram": "Instagram", "tiktok": "TikTok", "linkedin": "LinkedIn"}
    has_channels = any(channels_data.get(ch) for ch in channel_names)
    if has_channels:
        pdf.add_page()
        section_title("Distribution Channels")

        for ch_key, ch_title in channel_names.items():
            ch = channels_data.get(ch_key)
            if not ch:
                continue
            ensure_space(30)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*PURPLE)
            pdf.cell(CONTENT_W, 8, safe(ch_title), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(*LINE_GRAY)
            pdf.line(MARGIN, pdf.get_y(), MARGIN + 60, pdf.get_y())
            pdf.ln(3)

            # Render key fields generically
            skip_keys = {"generated_image_url", "image_prompt"}
            for key, val in ch.items():
                if key in skip_keys:
                    continue
                readable_key = key.replace("_", " ").title()
                if isinstance(val, list):
                    ensure_space(10)
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.set_text_color(*MID)
                    pdf.cell(CONTENT_W, 6, safe(readable_key), new_x="LMARGIN", new_y="NEXT")
                    for item in val:
                        ensure_space(7)
                        pdf.set_font("Helvetica", "", 9)
                        pdf.set_text_color(*DARK)
                        txt = safe(str(item)) if not isinstance(item, dict) else safe(json.dumps(item))
                        pdf.cell(5, 5, safe("\x95"))
                        pdf.multi_cell(CONTENT_W - 5, 5, txt)
                        pdf.ln(0.5)
                elif isinstance(val, str) and len(val) > 80:
                    ensure_space(14)
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.set_text_color(*MID)
                    pdf.cell(CONTENT_W, 6, safe(readable_key), new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(*DARK)
                    pdf.multi_cell(CONTENT_W, 5, safe(str(val)))
                    pdf.ln(1)
                else:
                    ensure_space(8)
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.set_text_color(*MID)
                    pdf.cell(50, 6, safe(readable_key))
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(*DARK)
                    pdf.cell(CONTENT_W - 50, 6, safe(str(val)), new_x="LMARGIN", new_y="NEXT")

            # Channel image if present
            ch_img = ch.get("generated_image_url", "")
            if ch_img:
                fname = ch_img.rsplit("/", 1)[-1] if "/" in ch_img else ch_img
                img_path = os.path.join(IMAGES_DIR, fname)
                if os.path.isfile(img_path):
                    ensure_space(90)
                    try:
                        pdf.image(img_path, x=MARGIN, w=80)
                        pdf.ln(4)
                    except Exception:
                        pass

            pdf.ln(6)

    # =====================================================================
    # FOOTER — Page numbers
    # =====================================================================
    total_pages = pdf.page
    for page_num in range(1, total_pages + 1):
        pdf.page = page_num
        pdf.set_y(-18)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*LIGHT)
        pdf.cell(CONTENT_W, 5, safe(f"Page {page_num} of {total_pages}"), align="C")

    # --- Output PDF -------------------------------------------------------
    try:
        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        print(f"  [export] PDF generated: {buf.getbuffer().nbytes} bytes")
        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"campaign-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf",
        )
    except Exception as e:
        print(f"  [export] PDF generation error: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Share via Email  (Microsoft Graph – /me/sendMail)
# ---------------------------------------------------------------------------
GRAPH_SEND_MAIL_URL = "https://graph.microsoft.com/v1.0/me/sendMail"


# ---------------------------------------------------------------------------
# Distribute to Channels  (4 specialised agents + optional image gen)
# ---------------------------------------------------------------------------


@app.route("/distribute", methods=["POST"])
def distribute_campaign():
    """SSE endpoint — runs the 4 channel agents and streams progress."""
    data = request.get_json() or {}

    strategy    = data.get("strategy", {})
    content     = data.get("content", {})
    visual      = data.get("visual", {})
    audience    = data.get("audience", {})
    performance = data.get("performance", {})

    # Build a comprehensive context blob for the channel agents
    campaign_context = (
        "=== CAMPAIGN BRIEF ===\n"
        f"Product: {data.get('product_name', 'N/A')}\n"
        f"Description: {data.get('product_description', 'N/A')}\n"
        f"Region: {data.get('target_region', 'N/A')}\n"
        f"Budget: ${data.get('budget', 'N/A')}\n\n"
        f"=== STRATEGY ===\n{json.dumps(strategy, indent=2)}\n\n"
        f"=== CONTENT ===\n{json.dumps(content, indent=2)}\n\n"
        f"=== AUDIENCE ===\n{json.dumps(audience, indent=2)}\n\n"
        f"=== PERFORMANCE ===\n{json.dumps(performance, indent=2)}"
    )

    channels_to_run = data.get("channels", ["email", "instagram", "tiktok", "linkedin"])

    def generate():
        channel_results = {}

        for channel in channels_to_run:
            agent = CHANNEL_AGENTS.get(channel)
            if not agent:
                continue

            # --- Activate node ---
            yield "data: " + json.dumps({
                "type": "channel_start",
                "channel": channel,
                "time": _timestamp(),
            }) + "\n\n"

            yield "data: " + json.dumps({
                "type": "log",
                "time": _timestamp(),
                "text": f"{channel.capitalize()} Agent activated — adapting content...",
                "color": channel if channel != "email" else "info",
            }) + "\n\n"

            try:
                prompt = (
                    f"Adapt the following marketing campaign for the {channel.upper()} channel.\n\n"
                    f"{campaign_context}\n\n"
                    "Return ONLY valid JSON."
                )

                future = asyncio.run_coroutine_threadsafe(
                    agent.run(prompt), _loop
                )
                raw = future.result(timeout=90)
                channel_data = _parse_agent_json(str(raw), channel)

                # --- Generate channel-specific image (Instagram / TikTok) ---
                if channel in IMAGE_CHANNELS:
                    img_prompt = channel_data.get("image_prompt", "")
                    if img_prompt:
                        yield "data: " + json.dumps({
                            "type": "log",
                            "time": _timestamp(),
                            "text": f"Generating {channel.capitalize()} image...",
                            "color": "visual",
                        }) + "\n\n"

                        try:
                            img_bytes = _generate_campaign_image(img_prompt, size="1024x1024")
                            img_filename = f"{channel}_{uuid.uuid4().hex[:8]}.png"
                            img_path = os.path.join(IMAGES_DIR, img_filename)
                            with open(img_path, "wb") as f:
                                f.write(img_bytes)
                            channel_data["generated_image_url"] = f"/generated_images/{img_filename}"

                            yield "data: " + json.dumps({
                                "type": "log",
                                "time": _timestamp(),
                                "text": f"{channel.capitalize()} image generated ({len(img_bytes)//1024} KB)",
                                "color": "visual",
                            }) + "\n\n"
                        except Exception as img_err:
                            print(f"  [{channel}] Image generation error: {img_err}")
                            yield "data: " + json.dumps({
                                "type": "log",
                                "time": _timestamp(),
                                "text": f"{channel.capitalize()} image failed — {img_err}",
                                "color": "default",
                            }) + "\n\n"

                channel_results[channel] = channel_data

                yield "data: " + json.dumps({
                    "type": "channel_complete",
                    "channel": channel,
                    "data": channel_data,
                    "time": _timestamp(),
                }) + "\n\n"

                yield "data: " + json.dumps({
                    "type": "log",
                    "time": _timestamp(),
                    "text": f"{channel.capitalize()} Agent completed",
                    "color": "default",
                }) + "\n\n"

            except Exception as e:
                print(f"  [{channel}] Agent error: {e}")
                yield "data: " + json.dumps({
                    "type": "channel_error",
                    "channel": channel,
                    "error": str(e),
                    "time": _timestamp(),
                }) + "\n\n"

        # --- All channels done ---
        yield "data: " + json.dumps({
            "type": "distribute_done",
            "results": channel_results,
        }) + "\n\n"

    return Response(generate(), content_type="text/event-stream")


def _build_campaign_html(data: dict) -> str:
    """Build a styled HTML email body from campaign results."""
    strategy  = data.get("strategy", {})
    content   = data.get("content", {})
    audience  = data.get("audience", {})
    perf      = data.get("performance", {})
    brief     = data.get("brief", {})

    # Inline-styled HTML email (most clients don't support <style> blocks)
    parts = []
    parts.append('<div style="font-family:Segoe UI,Helvetica,Arial,sans-serif;max-width:680px;margin:auto;color:#222;">')
    parts.append('<h1 style="color:#4527A0;margin-bottom:4px;">AI Marketing Campaign Report</h1>')
    if brief:
        parts.append(f'<p style="color:#888;font-size:13px;">Product: <b>{brief.get("product_name","")}</b> &middot; Region: {brief.get("region","")} &middot; Budget: {brief.get("budget","")}</p>')
    parts.append(f'<p style="color:#888;font-size:12px;">Generated {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>')
    parts.append('<hr style="border:none;border-top:2px solid #4527A0;margin:16px 0;">')

    # Strategy
    if strategy:
        parts.append('<h2 style="color:#4527A0;">Strategy</h2>')
        parts.append(f'<p>{strategy.get("strategic_overview","")}</p>')
        kpis = strategy.get("kpis", [])
        if kpis:
            parts.append('<table style="width:100%;border-collapse:collapse;margin:8px 0;">')
            parts.append('<tr style="background:#f5f0ff;"><th style="text-align:left;padding:6px;">KPI</th><th style="text-align:left;padding:6px;">Target</th></tr>')
            for k in kpis:
                parts.append(f'<tr><td style="padding:6px;border-bottom:1px solid #eee;">{k.get("name","")}</td>'
                             f'<td style="padding:6px;border-bottom:1px solid #eee;color:#4527A0;font-weight:600;">{k.get("target","")}</td></tr>')
            parts.append('</table>')
        if strategy.get("timeline"):
            parts.append(f'<p><b>Timeline:</b> {strategy["timeline"]}</p>')

    # Content
    if content:
        parts.append('<h2 style="color:#4527A0;">Content</h2>')
        parts.append(f'<h3 style="color:#4527A0;">{content.get("primary_headline","")}</h3>')
        for t in content.get("taglines", []):
            parts.append(f'<p style="margin:2px 0;">&bull; {t}</p>')
        for i,m in enumerate(content.get("campaign_messages",[]),1):
            parts.append(f'<p>{i}. {m}</p>')
        if content.get("tone"):
            parts.append(f'<p><em>Tone: {content["tone"]}</em></p>')

    # Audience
    if audience:
        parts.append('<h2 style="color:#4527A0;">Audience Segments</h2>')
        for seg in audience.get("segments",[]):
            parts.append(f'<p><b>{seg.get("name","")}</b> — <span style="color:#00BFA5;">{seg.get("potential_reach","")}</span></p>')
            tags = ", ".join(seg.get("tags",[]))
            if tags:
                parts.append(f'<p style="color:#888;font-size:12px;">{tags}</p>')
        if audience.get("total_reach"):
            parts.append(f'<p style="font-size:15px;color:#00BFA5;font-weight:700;">Total Reach: {audience["total_reach"]}</p>')

    # Performance
    if perf:
        parts.append('<h2 style="color:#4527A0;">Performance Projections</h2>')
        parts.append(f'<p><b>Conversion:</b> <span style="color:#00BFA5;">{perf.get("conversion_rate","")}</span>'
                     f' &middot; <b>ROI:</b> <span style="color:#4527A0;">{perf.get("estimated_roi","")}</span></p>')
        metrics = perf.get("metrics",[])
        if metrics:
            parts.append('<table style="width:100%;border-collapse:collapse;margin:8px 0;">')
            parts.append('<tr style="background:#f5f0ff;"><th style="text-align:left;padding:6px;">Metric</th><th style="text-align:left;padding:6px;">Value</th></tr>')
            for m in metrics:
                parts.append(f'<tr><td style="padding:6px;border-bottom:1px solid #eee;">{m.get("name","")}</td>'
                             f'<td style="padding:6px;border-bottom:1px solid #eee;color:#4527A0;font-weight:600;">{m.get("value","")}</td></tr>')
            parts.append('</table>')

    parts.append('<hr style="border:none;border-top:1px solid #ddd;margin:24px 0 8px;">')
    parts.append('<p style="font-size:11px;color:#aaa;">This report was generated by the AI Marketing Agent Pipeline Portal.</p>')
    parts.append('</div>')
    return "\n".join(parts)


@app.route("/share/email", methods=["POST"])
def share_email():
    """Send the campaign report via email using Microsoft Graph (me/sendMail)."""
    payload = request.get_json() or {}
    recipients = payload.get("recipients", [])  # list of email strings
    data       = payload.get("data", {})
    subject    = payload.get("subject", "AI Marketing Campaign Report")

    if not recipients:
        return jsonify({"error": "No recipients provided."}), 400

    # Build HTML body
    html_body = _build_campaign_html(data)

    # Get an access token for Microsoft Graph via the existing credential
    try:
        token = credential.get_token("https://graph.microsoft.com/.default")
    except Exception as e:
        print(f"  [email] Failed to acquire Graph token: {e}")
        return jsonify({"error": f"Authentication error – make sure you are signed in with `az login`: {e}"}), 401

    # Build Graph sendMail payload
    to_recipients = [{"emailAddress": {"address": r.strip()}} for r in recipients if r.strip()]
    graph_payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": to_recipients,
        },
        "saveToSentItems": True,
    }

    resp = http_requests.post(
        GRAPH_SEND_MAIL_URL,
        headers={
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
        },
        json=graph_payload,
        timeout=30,
    )

    if resp.status_code == 202:
        print(f"  [email] Sent campaign report to {', '.join(recipients)}")
        return jsonify({"ok": True})
    else:
        err = resp.text[:500]
        print(f"  [email] Graph API error {resp.status_code}: {err}")
        return jsonify({"error": f"Graph API {resp.status_code}: {err}"}), resp.status_code


# ---------------------------------------------------------------------------
# Agent-level Chat  (refine any agent output interactively)
# ---------------------------------------------------------------------------


@app.route("/chat/<agent_name>", methods=["POST"])
def chat_with_agent(agent_name):
    """Let the user refine a specific agent's output via follow-up messages."""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    current_data = data.get("current_data", {})
    brief_info = data.get("brief", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # --- Visual agent: regenerate image ---
    if agent_name == "visual":
        try:
            old_prompt = current_data.get("hero_prompt", "")
            # Ask the content agent to rewrite the image prompt
            rewrite_request = (
                f"You are an expert image prompt engineer.  The user currently has this "
                f"image prompt:\n\n{old_prompt}\n\n"
                f"The user says: \"{user_message}\"\n\n"
                f"Rewrite the image prompt to incorporate the user's request. "
                f"Return ONLY the new image prompt text, nothing else. "
                f"Keep the instruction 'Do NOT include any text, letters, or words in the image.' at the end."
            )
            future = asyncio.run_coroutine_threadsafe(
                content_agent.run(rewrite_request), _loop
            )
            new_prompt = str(future.result(timeout=60)).strip()
            # Strip fences
            if "```" in new_prompt:
                import re as _re
                m = _re.search(r"```(?:\w+)?\s*\n?(.*?)```", new_prompt, _re.DOTALL)
                if m:
                    new_prompt = m.group(1).strip()

            print(f"  [visual-chat] New prompt: {new_prompt[:120]}...")
            hero_bytes = _generate_campaign_image(new_prompt, size="1024x1024")
            hero_filename = f"hero_{uuid.uuid4().hex[:8]}.png"
            hero_path = os.path.join(IMAGES_DIR, hero_filename)
            with open(hero_path, "wb") as f:
                f.write(hero_bytes)

            visual_data = {
                "hero_image_url": f"/generated_images/{hero_filename}",
                "hero_prompt": new_prompt,
            }
            return jsonify({"ok": True, "data": visual_data})
        except Exception as e:
            print(f"  [visual-chat] Error: {e}")
            return jsonify({"error": str(e)}), 500

    # --- Text agents: refine output ---
    agent = MAIN_AGENTS.get(agent_name)
    if not agent:
        return jsonify({"error": f"Unknown agent: {agent_name}"}), 404

    try:
        current_json_str = json.dumps(current_data, indent=2)
        refine_prompt = (
            f"Campaign brief:\n{brief_info}\n\n"
            f"Here is your previous output (JSON):\n```json\n{current_json_str}\n```\n\n"
            f"The user asks: \"{user_message}\"\n\n"
            f"Please update your output to address the user's request. "
            f"Return your FULL updated output as valid JSON using the EXACT same schema. "
            f"Return ONLY the JSON object."
        )

        future = asyncio.run_coroutine_threadsafe(
            agent.run(refine_prompt), _loop
        )
        raw = str(future.result(timeout=90))
        parsed = _parse_agent_json(raw, agent_name)
        return jsonify({"ok": True, "data": parsed})
    except Exception as e:
        print(f"  [{agent_name}-chat] Error: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Channel Preview  (generate tailored content for a single channel)
# ---------------------------------------------------------------------------

@app.route("/channel/preview/<channel>", methods=["POST"])
def channel_preview(channel):
    """Invoke the channel agent for a single channel and return tailored content."""
    channel = channel.lower()
    agent = CHANNEL_AGENTS.get(channel)
    if not agent:
        return jsonify({"error": f"Unknown channel: {channel}"}), 404

    data = request.get_json() or {}

    strategy    = data.get("strategy", {})
    content     = data.get("content", {})
    visual      = data.get("visual", {})
    audience    = data.get("audience", {})
    performance = data.get("performance", {})

    campaign_context = (
        "=== CAMPAIGN BRIEF ===\n"
        f"Product: {data.get('product_name', 'N/A')}\n"
        f"Description: {data.get('product_description', 'N/A')}\n"
        f"Region: {data.get('target_region', 'N/A')}\n"
        f"Budget: ${data.get('budget', 'N/A')}\n\n"
        f"=== STRATEGY ===\n{json.dumps(strategy, indent=2)}\n\n"
        f"=== CONTENT ===\n{json.dumps(content, indent=2)}\n\n"
        f"=== AUDIENCE ===\n{json.dumps(audience, indent=2)}\n\n"
        f"=== PERFORMANCE ===\n{json.dumps(performance, indent=2)}"
    )

    try:
        prompt = (
            f"Adapt the following marketing campaign for the {channel.upper()} channel.\n\n"
            f"{campaign_context}\n\n"
            "Return ONLY valid JSON."
        )
        future = asyncio.run_coroutine_threadsafe(agent.run(prompt), _loop)
        raw = str(future.result(timeout=90))
        channel_data = _parse_agent_json(raw, channel)

        # Generate image for visual channels
        if channel in IMAGE_CHANNELS:
            img_prompt = channel_data.get("image_prompt", "")
            if img_prompt:
                try:
                    img_bytes = _generate_campaign_image(img_prompt, size="1024x1024")
                    img_filename = f"{channel}_{uuid.uuid4().hex[:8]}.png"
                    img_path = os.path.join(IMAGES_DIR, img_filename)
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)
                    channel_data["generated_image_url"] = f"/generated_images/{img_filename}"
                except Exception as img_err:
                    print(f"  [{channel}] Image generation error: {img_err}")

        return jsonify({"ok": True, "channel": channel, "data": channel_data})
    except Exception as e:
        print(f"  [{channel}-preview] Error: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  AI Marketing Agent Pipeline Portal")
    print("=" * 60)
    print(f"  Model  : {DEPLOYMENT_NAME}")
    print(f"  Open   : http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
