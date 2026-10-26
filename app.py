from flask import Flask, render_template_string, request, jsonify
from carbon_calculator import calculate_reduction, get_action_options
from datetime import date
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Carbon Diary</title>
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#194d37">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Carbon Diary">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="/static/icon-192.png">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    background: #f6f8f4;
    color: #24352b;
    line-height: 1.6;
}
header {
    background: linear-gradient(135deg, #194d37, #347653);
    color: white;
    padding: 40px 20px;
    text-align: center;
    box-shadow: 0 4px 18px rgba(31, 77, 53, 0.12);
}
.hero-label {
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 3px;
    color: #d6f0dc;
    margin: 0 0 10px;
}

header h1 {
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -1px;
    margin: 0 0 10px;
}

.hero-description {
    font-size: 16px;
    color: #e3f1e7;
    margin: 0;
}
main { max-width: 900px; margin: 30px auto; padding: 0 18px; }
.card {
    background: #ffffff;
    padding: 26px;
    border: 1px solid #e7eee6;
    border-radius: 20px;
    margin-bottom: 24px;
    box-shadow: 0 6px 24px rgba(35, 72, 48, 0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
}
.number {
    color: #247348;
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -1px;
    margin: 8px 0;
    line-height: 1.3;
}
label { display: block; margin: 14px 0 7px; font-weight: 600; }
input, select {
    width: 100%;
    padding: 13px 14px;
    border: 1px solid #d5dfd4;
    border-radius: 12px;
    font-size: 16px;
    background: #ffffff;
    color: #24352b;
    outline: none;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

input:focus, select:focus {
    border-color: #399563;
    box-shadow: 0 0 0 3px rgba(57, 149, 99, 0.12);
}
button {
    background: linear-gradient(135deg, #28784e, #399563);
    color: white;
    border: none;
    padding: 13px 22px;
    border-radius: 12px;
    cursor: pointer;
    font-size: 15px;
    font-weight: 700;
    box-shadow: 0 4px 10px rgba(40, 120, 78, 0.18);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
button:hover {
    background: #195c39;
    transform: translateY(-2px);
    box-shadow: 0 7px 16px rgba(40, 120, 78, 0.24);
}
button:active {
    transform: translateY(0);
}
.delete-btn { background: #a83d3d; padding: 7px 10px; }
.entry {
    border-bottom: 1px solid #e6ece4;
    padding: 18px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    border-radius: 10px;
    transition: background 0.2s ease;
}

.entry:hover {
    background: #f6f9f5;
}
.entry:last-child { border-bottom: none; }
.small { color: #6b796d; font-size: 13px; }
.message { margin-top: 12px; color: #28784e; }
footer { text-align: center; padding: 24px; color: #718075; }
</style>
</head>
<body>
<header>
    <p class="hero-label">MY GREEN LIFE</p>
    <h1>🌱 Carbon Diary</h1>
    <p class="hero-description">
        작은 실천이 모여 만드는 더 푸른 지구
    </p>
</header>

<main>
    <section class="card">
        <h2>오늘의 탄소 다이어리</h2>
        <p>친환경 행동을 기록하고 나의 실천을 확인해 보세요.</p>
        <p class="small">탄소 감축량은 예시 계수에 기반한 추정치입니다.</p>
    </section>

    <section class="stats">
        <div class="card">
            <h3>오늘의 감축량</h3>
            <div class="number" id="todayTotal">0 kg</div>
            <p class="small">CO₂e 추정치</p>
        </div>
        <div class="card">
            <h3>누적 감축량</h3>
            <div class="number" id="allTotal">0 kg</div>
            <p class="small">전체 기록 기준</p>
        </div>
        <div class="card">
            <h3>실천 횟수</h3>
            <div class="number" id="entryCount">0회</div>
            <p class="small">등록한 기록 수</p>
        </div>
        <div class="card">
            <h3>이번 주 감축량</h3>
            <div class="number" id="weeklyTotal">0 kg</div>
            <p class="small">이번 주 월요일부터</p>
        </div>
        <div class="card">
            <h3>이번 달 감축량</h3>
            <div class="number" id="monthlyTotal">0 kg</div>
            <p class="small">이번 달 기록 기준</p>
        </div>
    </section>

    <section class="card">
        <h2>✍️ 친환경 행동 기록하기</h2>
        <form id="entryForm">
            <label for="action">실천한 행동</label>
            <select id="action" required></select>

            <label for="amount">수량</label>
            <input id="amount" type="number" min="0.01" max="10000"
                   step="any" placeholder="예: 2" required>

            <label for="entryDate">날짜</label>
            <input id="entryDate" type="date" required>

            <label for="memo">메모 (선택)</label>
            <input id="memo" type="text" maxlength="200"
                   placeholder="예: 학교까지 버스 이용">

            <br><br>
            <button type="submit">기록 추가하기</button>
            <p id="message" class="message" role="status"></p>
        </form>
    </section>

    <section class="card">
        <h2>📋 나의 실천 기록</h2>
        <div id="entries"><p>아직 기록이 없어요. 첫 실천을 추가해 보세요!</p></div>
    </section>
<section class="card">
    <h2>📈 날짜별 탄소 감축량</h2>
    <canvas id="dailyChart"></canvas>
</section>

<section class="card">
    <h2>🌱 행동별 탄소 감축량</h2>
    <canvas id="actionChart"></canvas>
</section>

<section class="card">
    <h2>🤖 AI 탄소 절약 코치</h2>
    <p>내 탄소 다이어리 기록을 분석하고 맞춤형 조언을 받아보세요.</p>

    <button type="button" id="coachButton">
        🌿 AI 맞춤 조언 받기
    </button>

    <div id="coachResult" style="margin-top: 16px; white-space: pre-wrap;">
        버튼을 누르면 나만의 탄소 절약 팁을 알려드릴게요!
    </div>
</section>

</main>

<footer>Carbon Diary · 지속 가능한 일상을 위한 작은 실천</footer>

<script>
const STORAGE_KEY = "carbonDiaryEntries";
const actionSelect = document.getElementById("action");
const form = document.getElementById("entryForm");
const message = document.getElementById("message");

let actions = [];

function loadEntries() {
    try {
        const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        return Array.isArray(data) ? data : [];
    } catch {
        return [];
    }
}

function saveEntries(entries) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

async function initialize() {
    try {
        const response = await fetch("/api/actions");
        if (!response.ok) throw new Error("행동 목록을 불러오지 못했습니다.");
        actions = await response.json();

        actionSelect.replaceChildren();
        actions.forEach(action => {
            const option = document.createElement("option");
            option.value = action.id;
            option.textContent = `${action.name} (${action.unit})`;
            actionSelect.appendChild(option);
        });

        document.getElementById("entryDate").value =
            new Date().toLocaleDateString("sv-SE");

        renderEntries();
    } catch (error) {
        message.textContent = error.message;
    }
}

function renderCharts(entries) {
    const dailyTotals = {};
    const actionTotals = {};

    entries.forEach(entry => {
        dailyTotals[entry.date] =
            (dailyTotals[entry.date] || 0) + entry.reduction;

        actionTotals[entry.name] =
            (actionTotals[entry.name] || 0) + entry.reduction;
    });

    if (window.dailyChartInstance) {
        window.dailyChartInstance.destroy();
    }

    if (window.actionChartInstance) {
        window.actionChartInstance.destroy();
    }

    window.dailyChartInstance = new Chart(
        document.getElementById("dailyChart"),
        {
            type: "bar",
            data: {
                labels: Object.keys(dailyTotals).sort(),
                datasets: [{
                    label: "탄소 감축량 (kg)",
                    data: Object.keys(dailyTotals).sort()
                        .map(date => dailyTotals[date])
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        }
    );

    window.actionChartInstance = new Chart(
        document.getElementById("actionChart"),
        {
            type: "doughnut",
            data: {
                labels: Object.keys(actionTotals),
                datasets: [{
                    label: "탄소 감축량 (kg)",
                    data: Object.values(actionTotals)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        }
    );
}
function renderEntries() {
    const entries = loadEntries();
renderCharts(entries);    
const today = document.getElementById("entryDate").value ||
                  new Date().toLocaleDateString("sv-SE");

    const todayTotal = entries
        .filter(entry => entry.date === today)
        .reduce((sum, entry) => sum + entry.reduction, 0);

    const allTotal = entries.reduce((sum, entry) => sum + entry.reduction, 0);
    const now = new Date();
    const monday = new Date(now);
    const day = (now.getDay() + 6) % 7;
    monday.setDate(now.getDate() - day);
    monday.setHours(0, 0, 0, 0);

    const nextMonday = new Date(monday);
    nextMonday.setDate(monday.getDate() + 7);

    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);

    const weeklyTotal = entries
        .filter(entry => {
            const d = new Date(entry.date + "T00:00:00");
            return d >= monday && d < nextMonday;
        })
        .reduce((sum, entry) => sum + entry.reduction, 0);

    const monthlyTotal = entries
        .filter(entry => {
            const d = new Date(entry.date + "T00:00:00");
            return d >= monthStart && d < nextMonth;
        })
        .reduce((sum, entry) => sum + entry.reduction, 0);

    document.getElementById("todayTotal").textContent =
        todayTotal.toFixed(3) + " kg";
    document.getElementById("allTotal").textContent =
        allTotal.toFixed(3) + " kg";
    document.getElementById("entryCount").textContent =
        entries.length + "회";

    const container = document.getElementById("entries");
    container.replaceChildren();
    document.getElementById("weeklyTotal").textContent =
        weeklyTotal.toFixed(3) + " kg";
    document.getElementById("monthlyTotal").textContent =
        monthlyTotal.toFixed(3) + " kg";

    if (entries.length === 0) {
        container.textContent = "아직 기록이 없어요. 첫 실천을 추가해 보세요!";
        return;
    }

    [...entries].reverse().forEach(entry => {
        const row = document.createElement("div");
        row.className = "entry";

        const info = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = entry.name;

        const details = document.createElement("div");
        details.className = "small";
        details.textContent =
            `${entry.date} · 수량 ${entry.amount} ${entry.unit}`;

        const result = document.createElement("div");
        result.textContent = `약 ${entry.reduction.toFixed(3)} kg CO₂e`;

        info.append(title, details);
        if (entry.memo) {
            const memo = document.createElement("div");
            memo.className = "small";
            memo.textContent = entry.memo;
            info.appendChild(memo);
        }
        info.appendChild(result);

        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-btn";
        deleteButton.textContent = "삭제";
        deleteButton.addEventListener("click", () => deleteEntry(entry.id));

        row.append(info, deleteButton);
        container.appendChild(row);
    });
}

async function deleteEntry(id) {
    const entries = loadEntries().filter(entry => entry.id !== id);
    saveEntries(entries);
    renderEntries();
}

form.addEventListener("submit", async event => {
    event.preventDefault();
    message.textContent = "";

    const action = actionSelect.value;
    const amount = Number(document.getElementById("amount").value);
    const entryDate = document.getElementById("entryDate").value;
    const memo = document.getElementById("memo").value.trim();

    if (!Number.isFinite(amount) || amount <= 0 || amount > 10000) {
        message.textContent = "수량은 0보다 크고 10000 이하여야 합니다.";
        return;
    }

    if (!entryDate) {
        message.textContent = "날짜를 선택해 주세요.";
        return;
    }

    try {
        const response = await fetch("/api/calculate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({action, amount})
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "계산에 실패했습니다.");

        const selected = actions.find(item => item.id === action);
        const entry = {
            id: crypto.randomUUID(),
            date: entryDate,
            action,
            name: selected.name,
            unit: selected.unit,
            amount,
            memo,
            reduction: result.reduction
        };

        const entries = loadEntries();
        entries.push(entry);
        saveEntries(entries);

        form.reset();
        document.getElementById("entryDate").value =
            new Date().toLocaleDateString("sv-SE");

        renderEntries();
        message.textContent =
            `기록 완료! 예상 감축량은 ${result.reduction.toFixed(3)} kg CO₂e입니다.`;
    } catch (error) {
        message.textContent = error.message;
    }
});

document.getElementById("entryDate").addEventListener("change", renderEntries);
initialize();

async function loadGlobalCo2() {
    const status = document.getElementById("globalCo2Status");
    const yearSelect = document.getElementById("globalYear");
    const names = ["중국", "일본", "한국", "미국"];
    const colors = ["#4f7cac", "#7aa874", "#d9825b", "#8b78b8"];

    let totalChart;
    let perCapitaChart;
    let trendChart;

    async function getData(url) {
        const response = await fetch(url);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "데이터를 불러오지 못했습니다.");
        }
        return data.records;
    }

    async function render() {
        status.textContent = "데이터를 불러오는 중...";
        try {
            const year = yearSelect.value;
            const selected = await getData("/api/global-data?year=" + year);
            const all = await getData("/api/global-data");

            const countryOrder = ["China", "Japan", "South Korea", "United States"];
            const current = countryOrder.map(country =>
                selected.find(row => row.country === country)
            ).filter(Boolean);

            if (!current.length) {
                throw new Error("선택한 연도의 데이터가 없습니다.");
            }

            const labels = current.map(row => row.country_ko);

            if (totalChart) totalChart.destroy();
            if (perCapitaChart) perCapitaChart.destroy();
            if (trendChart) trendChart.destroy();

            totalChart = new Chart(document.getElementById("globalTotalChart"), {
                type: "bar",
                data: {
                    labels,
                    datasets: [{
                        label: "총 CO₂ 배출량 (백만 톤)",
                        data: current.map(row => row.co2_million_tonnes),
                        backgroundColor: current.map(row => colors[countryOrder.indexOf(row.country)])
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });

            perCapitaChart = new Chart(document.getElementById("globalPerCapitaChart"), {
                type: "bar",
                data: {
                    labels,
                    datasets: [{
                        label: "1인당 CO₂ 배출량 (톤/명)",
                        data: current.map(row => row.co2_per_capita_tonnes),
                        backgroundColor: current.map(row => colors[countryOrder.indexOf(row.country)])
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });

            const trendCountries = ["South Korea", "United States", "China", "Japan"];
            const trendLabels = [...new Set(all.map(row => row.year))].sort((a, b) => a - b);
            const datasets = trendCountries.map((country, i) => {
                const rows = all.filter(row => row.country === country);
                const byYear = new Map(rows.map(row => [row.year, row.co2_million_tonnes]));
                return {
                    label: rows[0]?.country_ko || country,
                    data: trendLabels.map(y => byYear.has(y) ? byYear.get(y) : null),
                    borderColor: colors[[2, 3, 0, 1][i]],
                    backgroundColor: colors[[2, 3, 0, 1][i]],
                    spanGaps: false,
                    tension: 0.2
                };
            });

            trendChart = new Chart(document.getElementById("globalTrendChart"), {
                type: "line",
                data: { labels: trendLabels, datasets },
                options: {
                    responsive: true,
                    interaction: { mode: "index", intersect: false },
                    scales: { y: { beginAtZero: true } }
                }
            });

            status.textContent = year + "년 데이터 · " + current.length +
                "개 국가 · 단위: 백만 톤 CO₂ / 톤 CO₂/명";
        } catch (error) {
            status.textContent = "데이터를 불러오지 못했어요: " + error.message;
        }
    }

    yearSelect.addEventListener("change", render);
    await render();
}

document.addEventListener("DOMContentLoaded", loadGlobalCo2);

document.getElementById("coachButton").addEventListener("click", async () => {
    const button = document.getElementById("coachButton");
    const result = document.getElementById("coachResult");
    const entries = loadEntries();

    if (!entries.length) {
        result.textContent = "먼저 탄소 다이어리에 친환경 행동을 기록해 주세요!";
        return;
    }

    button.disabled = true;
    result.textContent = "🌱 기록을 분석하고 있어요. 잠시만 기다려 주세요!";

    try {
        const response = await fetch("/api/coach", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ entries: entries })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "AI 조언을 불러오지 못했어요.");
        }

        result.textContent = data.advice;
    } catch (error) {
        result.textContent = error.message || "오류가 발생했어요. 다시 시도해 주세요.";
    } finally {
        button.disabled = false;
    }
});

</script>

<section id="globalCo2Section" style="max-width:1100px;margin:40px auto;padding:24px;background:white;border-radius:18px;">
  <h2>🌏 국가별 탄소 배출량 비교</h2>
  <p>Our World in Data 공개 자료 · 1990~2024년</p>
  <label for="globalYear">비교 연도</label>
  <select id="globalYear">
    <option value="2024" selected>2024년</option>
    <option value="2023">2023년</option>
    <option value="2022">2022년</option>
    <option value="2021">2021년</option>
    <option value="2020">2020년</option>
    <option value="2015">2015년</option>
    <option value="2010">2010년</option>
    <option value="2000">2000년</option>
    <option value="1990">1990년</option>
  </select>
  <p id="globalCo2Status" role="status">데이터를 불러오는 중...</p>
  <h3>총 CO₂ 배출량 (백만 톤)</h3>
  <canvas id="globalTotalChart"></canvas>
  <h3 style="margin-top:28px;">1인당 CO₂ 배출량 (톤/명)</h3>
  <canvas id="globalPerCapitaChart"></canvas>
  <h3 style="margin-top:28px;">연도별 배출량 추이 (백만 톤)</h3>
  <canvas id="globalTrendChart"></canvas>
  <p style="font-size:12px;color:#65746a;margin-top:18px;">
    출처: Our World in Data, CO₂ emissions. 총배출량과 1인당 배출량은 서로 다른 지표입니다.
  </p>
</section>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/actions")
def actions():
    return jsonify(get_action_options())


@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = request.get_json(silent=True) or {}

    try:
        action = data.get("action")
        amount = data.get("amount")
        reduction = calculate_reduction(action, amount)
        return jsonify({"reduction": reduction})
    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

@app.route("/api/coach", methods=["POST"])
def ai_coach():
    data = request.get_json(silent=True) or {}
    entries = data.get("entries", [])

    if not isinstance(entries, list):
        return jsonify({"error": "기록 형식이 올바르지 않아요."}), 400

    if not entries:
        return jsonify({"error": "먼저 탄소 다이어리에 기록을 추가해 주세요."}), 400

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": ".env 파일에서 API 키를 확인해 주세요."}), 500

    try:
        records = []
        for entry in entries[-100:]:
            if not isinstance(entry, dict):
                continue

            records.append({
                "날짜": str(entry.get("date", ""))[:20],
                "행동": str(entry.get("name", ""))[:100],
                "감축량(kg)": entry.get("reduction", 0)
            })

        if not records:
            return jsonify({"error": "분석할 수 있는 기록이 없어요."}), 400

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"""
너는 친절한 탄소 절약 코치야.
아래 사용자의 탄소 다이어리 기록을 바탕으로 한국어로 답해 줘.

기록: {records}

다음 내용을 포함해 줘.
1. 잘 실천하고 있는 점
2. 기록에서 발견되는 습관
3. 앞으로 실천할 수 있는 구체적인 행동 2가지

친절하고 부담 없는 말투로 5~8문장 이내로 작성해 줘.
기록에 없는 사실은 추측하지 말고, 감축량 수치는 참고값이라는 점을 고려해 줘.
"""
        )

        advice = response.text
        if not advice:
            return jsonify({"error": "AI 답변이 비어 있어요. 다시 시도해 주세요."}), 502

        return jsonify({"advice": advice})

    except Exception:
        app.logger.exception("AI 코치 요청 실패")
        return jsonify({
            "error": "AI 조언을 불러오지 못했어요. API 키와 모델 설정을 확인해 주세요."
        }), 502

if __name__ == "__main__":
    app.run(debug=True, port=5000)


@app.route("/api/global-data")
def global_data():
    import pandas as pd

    data_path = os.path.join(os.path.dirname(__file__), "global_co2_data.csv")

    if not os.path.exists(data_path):
        return jsonify({"error": "탄소 배출량 데이터 파일을 찾을 수 없습니다."}), 500

    countries = {
        "South Korea": "한국",
        "United States": "미국",
        "China": "중국",
        "Japan": "일본",
    }

    try:
        df = pd.read_csv(data_path)
        selected = request.args.get("country", "")
        year = request.args.get("year", type=int)

        if selected and selected not in countries:
            return jsonify({"error": "지원하지 않는 국가입니다."}), 400

        if year is not None and not 1990 <= year <= 2024:
            return jsonify({"error": "연도는 1990~2024년 사이여야 합니다."}), 400

        if selected:
            df = df[df["country"] == selected]

        if year is not None:
            df = df[df["year"] == year]

        df = df.sort_values(["year", "country"])

        records = []
        for _, row in df.iterrows():
            records.append({
                "country": row["country"],
                "country_ko": countries[row["country"]],
                "year": int(row["year"]),
                "co2_million_tonnes": round(float(row["co2"]), 3),
                "co2_per_capita_tonnes": round(float(row["co2_per_capita"]), 3),
            })

        return jsonify({
            "source": "Our World in Data — CO₂ emissions",
            "unit_total": "백만 톤 CO₂",
            "unit_per_capita": "톤 CO₂/명",
            "records": records,
        })

    except (OSError, ValueError, KeyError) as error:
        return jsonify({"error": f"데이터 처리 중 오류가 발생했습니다: {error}"}), 500
