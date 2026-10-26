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
