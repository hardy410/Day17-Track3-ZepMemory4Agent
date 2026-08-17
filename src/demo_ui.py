"""Streamlit UI for tracing the Lab 17 memory pipeline end to end."""

from __future__ import annotations

import html
import os
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import requests
import streamlit as st

from src.config import settings
from src.llm import SYSTEM_INSTRUCTION, gemini_available, generate_reply
from src.memory_student import StudentMemory
from src.router import route_with_llm
from src.short_term import ShortTermMemory
from src.utils import estimate_tokens, load_dataset, load_json, normalize
from src.zep_common import get_zep_client

GOLDEN_V3_PATH = _ROOT / "data" / "golden_eval_v3.json"

LAYER_META = {
    "short_term": {
        "label": "Ngắn hạn",
        "color": "#2563eb",
        "source": "Thread hiện tại",
        "purpose": "Lượt chat gần đây, bản tóm tắt và các ràng buộc cần ghi nhớ",
    },
    "long_term": {
        "label": "Dài hạn",
        "color": "#07845d",
        "source": "Graph của người dùng",
        "purpose": "Sở thích, dự án, deadline và fact riêng của người dùng",
    },
    "episodic": {
        "label": "Trải nghiệm",
        "color": "#c66a0a",
        "source": "Episode của người dùng",
        "purpose": "Các lần thử, kết quả và bài học trong quá khứ",
    },
    "semantic": {
        "label": "Kiến thức chung",
        "color": "#7b3fb3",
        "source": "Knowledge graph dùng chung",
        "purpose": "Policy, playbook và kiến thức miền dùng chung",
    },
}

CSS = """
<style>
:root {
    --ink: #17202a;
    --muted: #667085;
    --line: #d9dee7;
    --surface: #f7f8fa;
    --success: #087a55;
    --danger: #b42318;
}
.block-container { padding-top: 1.35rem; padding-bottom: 3rem; max-width: 1380px; }
h1, h2, h3 { letter-spacing: 0 !important; }
[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
.trace-header { border-bottom: 1px solid var(--line); padding: .25rem 0 1rem; margin-bottom: 1rem; }
.trace-eyebrow { color: #475467; font-size: .76rem; font-weight: 700; text-transform: uppercase; }
.trace-title { color: var(--ink); font-size: 2rem; font-weight: 760; line-height: 1.15; margin: .28rem 0; }
.trace-subtitle { color: var(--muted); font-size: .95rem; }
.case-panel { border: 1px solid var(--line); border-left: 4px solid #17202a; border-radius: 6px;
    padding: 1rem 1.1rem; background: #fff; margin-bottom: .8rem; }
.case-query { color: var(--ink); font-size: 1.04rem; line-height: 1.58; margin: .65rem 0 .45rem; }
.meta-line { color: var(--muted); font-size: .82rem; }
.chip { display: inline-flex; align-items: center; min-height: 24px; padding: 2px 8px;
    border: 1px solid var(--line); border-radius: 5px; font-size: .76rem; font-weight: 650;
    margin: 0 5px 5px 0; background: #fff; }
.marker-pass { color: var(--success); border-color: #83c9b0; background: #f1fbf7; }
.marker-fail { color: var(--danger); border-color: #f2a9a2; background: #fff6f5; }
.flow-step { border-top: 3px solid #98a2b3; padding: .55rem .1rem 0; min-height: 74px; }
.flow-step.active { border-color: #087a55; }
.flow-index { color: var(--muted); font-size: .7rem; font-weight: 700; text-transform: uppercase; }
.flow-label { color: var(--ink); font-size: .86rem; font-weight: 700; margin-top: .12rem; }
.flow-detail { color: var(--muted); font-size: .73rem; line-height: 1.25; }
.layer-heading { display: flex; gap: .55rem; align-items: center; }
.layer-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.small-muted { color: var(--muted); font-size: .78rem; }
.g20-heading { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:1.1rem 0 .65rem; }
.g20-heading h3 { margin:0; font-size:1.05rem; }
.g20-heading p { margin:0; color:var(--muted); font-size:.8rem; text-align:right; }
.g20-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
.g20-node { border:1px solid var(--line); border-top:4px solid var(--node-color); border-radius:6px;
    padding:.8rem .85rem; background:#fff; min-height:218px; }
.g20-node-head { display:flex; justify-content:space-between; gap:.5rem; align-items:center; }
.g20-node h4 { margin:0; font-size:.92rem; color:var(--ink); }
.g20-state { font-size:.68rem; font-weight:750; color:var(--success); text-transform:uppercase; }
.g20-state.waiting { color:var(--muted); }
.g20-state.failed { color:var(--danger); }
.g20-row { display:grid; grid-template-columns:74px minmax(0,1fr); gap:.45rem; padding:.38rem 0;
    border-bottom:1px solid #edf0f4; font-size:.76rem; line-height:1.35; }
.g20-row:last-child { border-bottom:0; }
.g20-key { color:var(--muted); }
.g20-value { color:var(--ink); font-weight:600; overflow-wrap:anywhere; }
.g20-evidence { margin-top:.5rem; padding:.48rem .55rem; border-radius:5px; background:var(--surface);
    font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.74rem; color:var(--ink); }
.g20-assembly { display:grid; grid-template-columns:1fr auto; gap:1rem; align-items:center; margin:.65rem 0 1rem;
    padding:.7rem .85rem; border:1px solid var(--line); border-left:4px solid #17202a; border-radius:6px; }
.g20-assembly-main { font-size:.8rem; color:var(--ink); }
.g20-assembly-main b { display:block; margin-bottom:.14rem; }
.g20-assembly-result { color:var(--success); font-size:.82rem; font-weight:800; white-space:nowrap; }
@media (max-width: 760px) {
    .g20-grid { grid-template-columns:1fr; }
    .g20-heading { align-items:start; flex-direction:column; }
    .g20-heading p { text-align:left; }
    .g20-assembly { grid-template-columns:1fr; }
}
div[data-testid="stMetric"] { border: 1px solid var(--line); border-radius: 6px; padding: .7rem .85rem; }
div[data-testid="stMetric"] label { color: var(--muted); }
div[data-testid="stExpander"] { border-radius: 6px; border-color: var(--line); }
.stButton button { border-radius: 6px; }
.stCodeBlock { border-radius: 6px; }
</style>
"""


def load_case_sets() -> dict[str, list[dict[str, Any]]]:
    """Load Golden V3 as the primary set and practice as a secondary set."""
    case_sets: dict[str, list[dict[str, Any]]] = {}
    if GOLDEN_V3_PATH.exists():
        case_sets["Golden V3"] = load_json(GOLDEN_V3_PATH).get("evaluations") or []
    case_sets["Bài luyện tập"] = list(load_dataset()["evaluations"])
    return case_sets


def format_case(case: dict[str, Any]) -> str:
    return case["id"]


def generate_demo_reply(
    memory_context: str,
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    """Generate a reply through the configured compatible gateway or native SDK."""
    base_url = os.getenv("GEMINI_BASE_URL", "").rstrip("/")
    if not base_url:
        return generate_reply(memory_context, history, user_message)

    grounding = (
        "Retrieved memory context for this turn:\n"
        "-------------------------------------\n"
        f"{memory_context.strip() or '(no memory retrieved)'}\n"
        "-------------------------------------\n\n"
        f"User message: {user_message}"
    )
    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    messages.extend(
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if msg.get("role") in {"user", "assistant"} and msg.get("content")
    )
    messages.append({"role": "user", "content": grounding})

    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.gemini_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.gemini_model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800,
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return str(payload["choices"][0]["message"]["content"]).strip()


def find_thread_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    fixture = case.get("fixture_messages")
    if fixture is not None:
        return list(fixture)
    for user in load_dataset()["users"]:
        if user["user_id"] != case["user_id"]:
            continue
        for session in user.get("sessions", []):
            if session["thread_id"] == case["thread_id"]:
                return list(session.get("messages", []))
    return []


def retrieve_for_case(
    memory: StudentMemory,
    case: dict[str, Any],
    extra_messages: list[dict[str, str]],
) -> dict[str, Any]:
    """Run the selected layers and retain evidence at every pipeline stage."""
    started = time.perf_counter()
    base_messages = find_thread_messages(case)
    route = route_with_llm(case["query"])
    active_layers = route.layers
    layer_timings: dict[str, float] = {}
    short_stats: dict[str, int] = {}
    layers = {name: "" for name in LAYER_META}

    if "short_term" in active_layers:
        layer_started = time.perf_counter()
        short_term = ShortTermMemory(
            strategy="sliding",
            max_recent_messages=6,
            pressure_tokens=450,
        )
        for message in [*base_messages, *extra_messages]:
            short_term.add(message["role"], message["content"])
        layers["short_term"] = short_term.render()
        short_stats = short_term.stats()
        layer_timings["short_term"] = (time.perf_counter() - layer_started) * 1000

    if "long_term" in active_layers:
        layer_started = time.perf_counter()
        layers["long_term"] = memory.retrieve_long_term(
            user_id=case["user_id"],
            thread_id=case["thread_id"],
            query=case["query"],
        )
        layer_timings["long_term"] = (time.perf_counter() - layer_started) * 1000

    if "episodic" in active_layers:
        layer_started = time.perf_counter()
        layers["episodic"] = memory.retrieve_episodic(
            user_id=case["user_id"],
            query=case["query"],
        )
        layer_timings["episodic"] = (time.perf_counter() - layer_started) * 1000

    if "semantic" in active_layers:
        layer_started = time.perf_counter()
        layers["semantic"] = memory.retrieve_semantic(
            graph_id=settings.semantic_graph_id,
            query=case["query"],
        )
        layer_timings["semantic"] = (time.perf_counter() - layer_started) * 1000

    merged_context, budget = memory.assemble_context(layers)
    trimmed_layers = {
        layer: memory.budget.trim(text, budget[layer]["limit_tokens"])
        for layer, text in layers.items()
    }
    return {
        "merged_context": merged_context,
        "layers": layers,
        "trimmed_layers": trimmed_layers,
        "budget": budget,
        "layer_timings": layer_timings,
        "short_term_stats": short_stats,
        "active_layers": active_layers,
        "route": route.to_dict(),
        "retrieval_latency_ms": (time.perf_counter() - started) * 1000,
    }


def score_context(case: dict[str, Any], context: str) -> dict[str, Any]:
    normalized = normalize(context)
    checks: list[dict[str, Any]] = []
    for marker in case.get("must_contain_all", []):
        found = normalize(marker) in normalized
        checks.append(
            {
                "Quy tắc": "Bắt buộc",
                "Marker": marker,
                "Kết quả": "Đã tìm thấy" if found else "Bị thiếu",
                "passed": found,
            }
        )
    for marker in case.get("must_not_contain", []):
        absent = normalize(marker) not in normalized
        checks.append(
            {
                "Quy tắc": "Không được có",
                "Marker": marker,
                "Kết quả": "Không xuất hiện" if absent else "Đã xuất hiện",
                "passed": absent,
            }
        )
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def marker_location(marker: str, layers: dict[str, str]) -> str:
    matches = [LAYER_META[name]["label"] for name, text in layers.items() if normalize(marker) in normalize(text)]
    return ", ".join(matches) or "Không truy xuất được"


def render_case_header(case: dict[str, Any], dataset_name: str) -> None:
    required = "".join(
        f'<span class="chip marker-pass">cần có: {html.escape(marker)}</span>'
        for marker in case.get("must_contain_all", [])
    )
    forbidden = "".join(
        f'<span class="chip marker-fail">không được có: {html.escape(marker)}</span>'
        for marker in case.get("must_not_contain", [])
    )
    st.markdown(
        f'<section class="case-panel"><div class="case-query">{html.escape(case.get("query", ""))}</div>'
        f'<div>{required}{forbidden}</div>'
        f'<div class="meta-line">{html.escape(dataset_name)} &nbsp;|&nbsp; '
        f'người dùng: {html.escape(case.get("user_id", "-"))} &nbsp;|&nbsp; '
        f'thread: {html.escape(case.get("thread_id", "-"))}</div></section>',
        unsafe_allow_html=True,
    )


def render_flow(result: dict[str, Any] | None, answer_ready: bool) -> None:
    active = result.get("active_layers", []) if result else []
    route_detail = " + ".join(LAYER_META[layer]["label"] for layer in active) if active else "Chưa chạy"
    steps = [
        ("01", "Câu hỏi", "Đầu vào của case", True),
        ("02", "LLM router", route_detail, bool(result)),
        ("03", "Truy xuất", "Đã thu thập bằng chứng" if result else "Chưa chạy", bool(result)),
        ("04", "Giới hạn", "Đã áp dụng 10 / 4 / 3 / 3" if result else "Chưa chạy", bool(result)),
        ("05", "Trả lời", "Câu trả lời đã sẵn sàng" if answer_ready else "Chưa chạy", answer_ready),
    ]
    columns = st.columns(5)
    for column, (index, label, detail, is_active) in zip(columns, steps):
        column.markdown(
            f'<div class="flow-step {"active" if is_active else ""}">'
            f'<div class="flow-index">Bước {index}</div>'
            f'<div class="flow-label">{html.escape(label)}</div>'
            f'<div class="flow-detail">{html.escape(detail)}</div></div>',
            unsafe_allow_html=True,
        )


def g20_demo_rows(result: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Build G20 display data from the actual retrieval result when available."""
    specs = [
        {
            "layer": "short_term",
            "query_used": "Không - chỉ đọc 14 fixture message",
            "source": "Thread hiện tại",
            "logic": "Giữ 6 message gần nhất; lưu lại ràng buộc bền vững",
            "marker": "HOLD-ALPHA-0900",
        },
        {
            "layer": "long_term",
            "query_used": "Có - toàn bộ query G20",
            "source": "User graph của Minh",
            "logic": "Context Block + tối đa 20 fact; không có LLM lọc",
            "marker": "NestJS",
        },
        {
            "layer": "semantic",
            "query_used": "Có - toàn bộ query G20",
            "source": "Knowledge graph dùng chung",
            "logic": "Tìm episode, limit 8; rút gọn và loại tài liệu trùng",
            "marker": "Idempotency-Key",
        },
    ]
    for spec in specs:
        layer = spec["layer"]
        if result:
            budget = result["budget"][layer]
            survived = normalize(spec["marker"]) in normalize(result["trimmed_layers"][layer])
            spec["tokens"] = f'{budget["raw_tokens"]} thô -> {budget["used_tokens"]} dùng / giới hạn {budget["limit_tokens"]}'
            spec["state"] = "Còn sau khi cắt" if survived else "Mất sau khi cắt"
            spec["passed"] = survived
        else:
            spec["tokens"] = "Có số liệu sau khi chạy"
            spec["state"] = "Chưa chạy"
            spec["passed"] = None
    return specs


def render_g20_map(result: dict[str, Any] | None, score: dict[str, Any] | None) -> None:
    rows = g20_demo_rows(result)
    cards: list[str] = []
    for index, row in enumerate(rows, start=1):
        layer = row["layer"]
        meta = LAYER_META[layer]
        if row["passed"] is None:
            state_class = " waiting"
        elif row["passed"] is False:
            state_class = " failed"
        else:
            state_class = ""
        cards.append(
            f'<article class="g20-node" style="--node-color:{meta["color"]}">'
            f'<div class="g20-node-head"><h4>{index:02d}. {html.escape(meta["label"])}</h4>'
            f'<span class="g20-state{state_class}">{html.escape(row["state"])}</span></div>'
            f'<div class="g20-row"><span class="g20-key">Dùng query</span><span class="g20-value">{html.escape(row["query_used"])}</span></div>'
            f'<div class="g20-row"><span class="g20-key">Đọc từ</span><span class="g20-value">{html.escape(row["source"])}</span></div>'
            f'<div class="g20-row"><span class="g20-key">Logic code</span><span class="g20-value">{html.escape(row["logic"])}</span></div>'
            f'<div class="g20-row"><span class="g20-key">Ngân sách</span><span class="g20-value">{html.escape(row["tokens"])}</span></div>'
            f'<div class="g20-evidence">cần lấy: {html.escape(row["marker"])}</div></article>'
        )

    if score is None:
        final_state = "Chưa chạy"
    else:
        passed = sum(1 for check in score["checks"] if check["passed"])
        final_state = f'{passed}/{len(score["checks"])} điều kiện đạt'

    st.markdown(
        '<div class="g20-heading"><h3>Bản đồ bằng chứng G20</h3>'
        '<p>Các lớp do LLM router chọn, mỗi đường truy xuất hoạt động độc lập</p></div>'
        f'<div class="g20-grid">{"".join(cards)}</div>'
        '<div class="g20-assembly"><div class="g20-assembly-main">'
        '<b>Ghép cuối: Ngắn hạn -> Dài hạn -> Kiến thức chung</b>'
        'Mỗi lớp bị giới hạn riêng trước khi ghép. Priority chỉ điều khiển thứ tự block; token thừa không được chia lại.'
        f'</div><div class="g20-assembly-result">{html.escape(final_state)}</div></div>',
        unsafe_allow_html=True,
    )

    with st.expander("Ghi chú thuyết trình G20", expanded=False):
        st.markdown(
            """
1. **Chọn lớp:** LLM router chỉ đọc query và chọn `short_term + long_term + semantic`. Golden V3 chỉ được dùng sau đó để chấm lựa chọn này.
2. **Ngắn hạn:** không dùng query để tìm kiếm. Lớp này rút gọn 14 fixture message và giữ `HOLD-ALPHA-0900` trong durable notes.
3. **Dài hạn:** toàn bộ query được đưa vào thread tạm của Minh. Zep trả Context Block theo người dùng và tối đa 20 fact. Python có thể vẫn còn trong context; tại đây không có LLM lọc.
4. **Kiến thức chung:** cùng query đó tìm trong shared graph và lấy payment policy chứa `Idempotency-Key`.
5. **Cắt và ghép:** áp dụng giới hạn 10/4/3/3 rồi ghép theo priority. Benchmark kiểm tra ba marker bắt buộc và xác nhận không có `LOTUS-88`.
            """
        )


def render_trace(result: dict[str, Any], score: dict[str, Any]) -> None:
    raw_total = sum(item["raw_tokens"] for item in result["budget"].values())
    used_total = sum(item["used_tokens"] for item in result["budget"].values())
    reduction = max(0.0, 1 - (used_total / raw_total)) if raw_total else 0.0
    metrics = st.columns(4)
    metrics[0].metric("Truy xuất", "ĐẠT" if score["passed"] else "KHÔNG ĐẠT")
    metrics[1].metric("Độ trễ", f'{result["retrieval_latency_ms"]:.0f} ms')
    metrics[2].metric("Ngữ cảnh", f"{estimate_tokens(result['merged_context'])} token")
    metrics[3].metric("Rút gọn", f"{reduction:.1%}")

    tab_trace, tab_evidence, tab_context, tab_answer = st.tabs(
        ["Dòng xử lý", "Bằng chứng từng lớp", "Ngữ cảnh cuối", "Câu trả lời"]
    )

    with tab_trace:
        route = result["route"]
        route_source = "LLM" if route["source"] == "llm" else "Luật fallback"
        st.markdown(f"#### Router: {route_source}")
        st.write(route["reason"])
        st.caption("Lớp đã chọn: " + ", ".join(result["active_layers"]))
        if route.get("fallback_used"):
            st.warning("LLM router không khả dụng; pipeline đang dùng fallback xác định.")
        rows: list[dict[str, Any]] = []
        for layer in result["active_layers"]:
            budget = result["budget"][layer]
            meta = LAYER_META[layer]
            rows.append(
                {
                    "Lớp": meta["label"],
                    "Đọc từ": meta["source"],
                    "Vai trò": meta["purpose"],
                    "Token thô": budget["raw_tokens"],
                    "Token dùng": budget["used_tokens"],
                    "Giới hạn": budget["limit_tokens"],
                    "Độ trễ (ms)": round(result["layer_timings"].get(layer, 0.0), 1),
                }
            )
        st.dataframe(rows, hide_index=True, width="stretch")

        st.markdown("#### Kiểm tra bằng chứng")
        check_rows = [
            {
                "Quy tắc": check["Quy tắc"],
                "Marker": check["Marker"],
                "Nằm trong lớp": marker_location(check["Marker"], result["trimmed_layers"]),
                "Kết quả": check["Kết quả"],
            }
            for check in score["checks"]
        ]
        st.dataframe(check_rows, hide_index=True, width="stretch")
        if score["passed"]:
            st.success("Tất cả bằng chứng bắt buộc vẫn còn sau khi truy xuất và cắt theo ngân sách.")
        else:
            st.error("Ngữ cảnh cuối chưa đáp ứng tất cả điều kiện kiểm tra.")

        if result.get("short_term_stats"):
            stats = result["short_term_stats"]
            st.caption(
                "Rút gọn ngắn hạn: "
                f'giữ {stats.get("messages_kept", 0)} message, '
                f'{stats.get("durable_notes", 0)} durable note, '
                f'{stats.get("compactions", 0)} lần rút gọn.'
            )

    with tab_evidence:
        for layer in result["active_layers"]:
            meta = LAYER_META[layer]
            budget = result["budget"][layer]
            st.markdown(
                f'<div class="layer-heading"><span class="layer-dot" style="background:{meta["color"]}"></span>'
                f'<strong>{html.escape(meta["label"])}</strong>'
                f'<span class="small-muted">{html.escape(meta["source"])} | '
                f'{budget["raw_tokens"]} token thô -> {budget["used_tokens"]} token dùng</span></div>',
                unsafe_allow_html=True,
            )
            raw_col, used_col = st.columns(2)
            with raw_col:
                st.caption("Output truy xuất thô")
                st.code(result["layers"][layer] or "(trống)", language="text", wrap_lines=True)
            with used_col:
                st.caption("Sau khi áp dụng ngân sách lớp")
                st.code(result["trimmed_layers"][layer] or "(trống)", language="text", wrap_lines=True)
            st.divider()

    with tab_context:
        st.caption("Đây là chính xác memory context được đưa vào bước tạo câu trả lời.")
        st.code(result["merged_context"] or "(trống)", language="xml", wrap_lines=True)

    with tab_answer:
        answer = st.session_state.get("last_answer", "")
        if answer:
            st.markdown(answer)
            st.caption(f'Thời gian tạo câu trả lời: {st.session_state.get("answer_latency_ms", 0.0):.0f} ms')
        elif gemini_available():
            st.info("Bật tạo câu trả lời và chạy lại case để hoàn thành bước này.")
        else:
            st.warning("Dịch vụ tạo câu trả lời chưa được cấu hình. Dòng truy xuất vẫn có thể sử dụng.")


def main() -> None:
    st.set_page_config(page_title="Lab 17 - Dòng xử lý bộ nhớ", page_icon=":material/account_tree:", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    case_sets = load_case_sets()
    if not case_sets:
        st.error("Không tìm thấy case đánh giá nào.")
        return

    with st.sidebar:
        st.subheader("Điều khiển demo")
        dataset_names = list(case_sets)
        dataset_name = st.radio("Bộ dữ liệu", dataset_names, index=0)
        cases = case_sets[dataset_name]
        if not cases:
            st.error("Bộ dữ liệu đã chọn đang trống.")
            return

        labels = [format_case(case) for case in cases]
        default_index = next((i for i, case in enumerate(cases) if case["id"] == "G20"), 0)
        chosen = st.selectbox("Case kiểm thử", labels, index=default_index)
        case = cases[labels.index(chosen)]
        generate_answer = st.toggle(
            "Tạo câu trả lời",
            value=False,
            help="Khi bật, memory context đã ghép sẽ được gửi tới dịch vụ tạo câu trả lời đã cấu hình.",
        )
        run_clicked = st.button(
            "Chạy toàn bộ quy trình",
            type="primary",
            width="stretch",
            icon=":material/play_arrow:",
        )
        st.divider()
        zep_ok = bool(settings.zep_api_key)
        answer_ok = gemini_available()
        st.caption(f'Kết nối Zep: {"sẵn sàng" if zep_ok else "chưa cấu hình"}')
        st.caption(f'Dịch vụ trả lời: {"sẵn sàng" if answer_ok else "chưa cấu hình"}')

    state_key = f"{dataset_name}:{case['id']}"
    if st.session_state.get("case_key") != state_key:
        st.session_state.case_key = state_key
        st.session_state.chat = []
        for key in ("last_result", "last_answer", "last_score", "answer_latency_ms"):
            st.session_state.pop(key, None)

    st.markdown(
        '<header class="trace-header"><div class="trace-eyebrow">Lab 17 / dòng thực thi bộ nhớ</div>'
        '<div class="trace-title">Tác tử bộ nhớ đa tầng</div>'
        '<div class="trace-subtitle">Theo dõi một câu hỏi từ đầu vào, truy xuất, cắt gọn, tạo ngữ cảnh đến đánh giá.</div></header>',
        unsafe_allow_html=True,
    )
    render_case_header(case, dataset_name)
    render_flow(st.session_state.get("last_result"), bool(st.session_state.get("last_answer")))
    if case["id"] == "G20":
        render_g20_map(
            st.session_state.get("last_result"),
            st.session_state.get("last_score"),
        )

    pipeline_completed = False
    if run_clicked:
        if not zep_ok:
            st.error("Zep chưa được cấu hình cho case đã chọn.")
        else:
            try:
                with st.status("Đang chạy pipeline bộ nhớ...", expanded=True) as status:
                    memory = StudentMemory(get_zep_client())
                    result = retrieve_for_case(memory, case, st.session_state.chat)
                    st.write("Đã truy xuất xong. Đang áp dụng ngân sách cho từng lớp.")
                    score = score_context(case, result["merged_context"])
                    st.session_state.last_result = result
                    st.session_state.last_score = score

                    if generate_answer and answer_ok:
                        answer_started = time.perf_counter()
                        st.session_state.last_answer = generate_demo_reply(
                            result["merged_context"], st.session_state.chat, case["query"]
                        )
                        st.session_state.answer_latency_ms = (time.perf_counter() - answer_started) * 1000
                        st.write("Đã tạo câu trả lời dựa trên memory context.")
                    else:
                        st.session_state.last_answer = ""
                        st.session_state.answer_latency_ms = 0.0
                    status.update(label="Pipeline đã hoàn thành", state="complete", expanded=False)
                    pipeline_completed = True
            except Exception as exc:  # noqa: BLE001
                st.exception(exc)

    if pipeline_completed:
        st.rerun()

    result = st.session_state.get("last_result")
    if result:
        render_trace(result, st.session_state["last_score"])
    else:
        st.info("Chọn một case và chạy pipeline để xem toàn bộ dòng thực thi.")

    st.divider()
    with st.expander("Hội thoại tiếp nối", expanded=False):
        for message in st.session_state.get("chat", []):
            with st.chat_message(message["role"]):
                st.write(message["content"])

        prompt = st.chat_input("Đặt câu hỏi tiếp theo với vai trò người dùng này")
        if prompt:
            st.session_state.chat.append({"role": "user", "content": prompt})
            try:
                memory = StudentMemory(get_zep_client())
                follow_case = {**case, "query": prompt}
                follow = retrieve_for_case(memory, follow_case, st.session_state.chat)
                st.session_state.last_result = follow
                st.session_state.last_score = score_context(case, follow["merged_context"])
                if answer_ok:
                    answer_started = time.perf_counter()
                    reply = generate_demo_reply(follow["merged_context"], st.session_state.chat[:-1], prompt)
                    st.session_state.answer_latency_ms = (time.perf_counter() - answer_started) * 1000
                else:
                    reply = follow["merged_context"][:1500] or "Không truy xuất được memory nào."
                st.session_state.chat.append({"role": "assistant", "content": reply})
                st.session_state.last_answer = reply
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.exception(exc)


if __name__ == "__main__":
    main()
