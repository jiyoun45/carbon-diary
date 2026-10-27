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
    <h2>🎯 이번 달 탄소 감축 목표</h2>
    <p>이번 달에 달성하고 싶은 탄소 감축량을 설정해 보세요.</p>

    <label for="monthlyGoal">월간 목표 (kg CO₂e)</label>
    <input id="monthlyGoal" type="number" min="0.1" step="0.1" value="10" style="margin-bottom: 12px;">

    <button type="button" id="saveGoalButton">목표 저장하기</button>

    <div style="margin-top: 18px;">
        <p>이번 달 감축량: <strong id="goalCurrent">0 kg</strong></p>
        <p>목표 달성률: <strong id="goalRate">0%</strong></p>
        <div style="background:#e7eee6; height:14px; border-radius:10px; overflow:hidden;">
            <div id="goalProgress" style="width:0%; height:100%; background:#399563; transition:width .3s;"></div>
        </div>
        <p id="goalMessage" class="small">목표를 설정하고 친환경 실천을 기록해 보세요!</p>
    </div>
</section>

<section class="card">
    <h2>🏆 미션 & 보상</h2>
    <p>친환경 실천을 기록하고 배지를 모아 보세요!</p>

    <div class="stats">
        <div class="stat-card">
            <p>나의 레벨</p>
            <strong id="rewardLevel">🌱 새싹 Lv.1</strong>
        </div>
        <div class="stat-card">
            <p>실천 횟수</p>
            <strong id="rewardCount">0회</strong>
        </div>
        <div class="stat-card">
            <p>누적 감축량</p>
            <strong id="rewardReduction">0 kg</strong>
        </div>
    </div>

    <h3>🎯 도전 미션</h3>
    <div id="missionList">
        미션 정보를 불러오는 중이에요.
    </div>

    <h3>🎖️ 획득한 배지</h3>
    <div id="badgeList">
        아직 획득한 배지가 없어요.
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
    <h2>🔎 나의 탄소 절약 분석</h2>
    <p>지금까지 기록한 친환경 실천을 분석해 드려요.</p>

    <div class="stats">
        <div class="stat-card">
            <p>가장 효과적인 실천</p>
            <strong id="analysisBestAction">기록을 기다리는 중</strong>
        </div>
        <div class="stat-card">
            <p>가장 많이 감축한 유형</p>
            <strong id="analysisBestReduction">0 kg</strong>
        </div>
        <div class="stat-card">
            <p>전체 기록 중 감축량</p>
            <strong id="analysisTotal">0 kg</strong>
        </div>
    </div>

    <h3>실천 유형별 감축량</h3>
    <div id="analysisBreakdown">
        아직 기록이 없어요. 친환경 실천을 기록해 보세요!
    </div>

    <p id="analysisFeedback" class="small">
        실천 기록이 쌓이면 나만의 분석 결과가 표시돼요.
    </p>
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

const GOAL_STORAGE_KEY = "carbonDiaryMonthlyGoal";

function loadMonthlyGoal() {
    const savedGoal = Number(localStorage.getItem(GOAL_STORAGE_KEY));
    return Number.isFinite(savedGoal) && savedGoal > 0 ? savedGoal : 10;
}

function updateGoalProgress() {
    const goalInput = document.getElementById("monthlyGoal");
    const goal = loadMonthlyGoal();

    goalInput.value = goal;

    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();

    const monthlyTotal = loadEntries()
        .filter(entry => {
            const d = new Date(entry.date + "T00:00:00");
            return d.getFullYear() === year && d.getMonth() === month;
        })
        .reduce((sum, entry) => sum + Number(entry.reduction || 0), 0);

    const rate = monthlyTotal / goal * 100;
    const progress = Math.min(rate, 100);

    document.getElementById("goalCurrent").textContent =
        monthlyTotal.toFixed(3) + " kg";
    document.getElementById("goalRate").textContent =
        rate.toFixed(1) + "%";
    document.getElementById("goalProgress").style.width =
        progress + "%";

    document.getElementById("goalMessage").textContent =
        rate >= 100
            ? "🎉 이번 달 목표를 달성했어요!"
            : `목표까지 ${(goal - monthlyTotal).toFixed(3)} kg 남았어요.`;
}

document.getElementById("saveGoalButton").addEventListener("click", () => {
    const goal = Number(document.getElementById("monthlyGoal").value);

    if (!Number.isFinite(goal) || goal <= 0) {
        alert("목표는 0보다 큰 숫자로 입력해 주세요.");
        return;
    }

    localStorage.setItem(GOAL_STORAGE_KEY, String(goal));
    updateGoalProgress();
    alert("이번 달 목표를 저장했어요!");
});

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

function updatePersonalAnalysis(entries) {
    const bestActionEl = document.getElementById("analysisBestAction");
    const bestReductionEl = document.getElementById("analysisBestReduction");
    const totalEl = document.getElementById("analysisTotal");
    const breakdownEl = document.getElementById("analysisBreakdown");
    const feedbackEl = document.getElementById("analysisFeedback");

    if (!bestActionEl || !bestReductionEl || !totalEl || !breakdownEl || !feedbackEl) {
        return;
    }

    const totals = {};
    let totalReduction = 0;

    entries.forEach(entry => {
        const reduction = Number(entry.reduction) || 0;
        const actionName = entry.name || entry.action || "기타 실천";

        totals[actionName] = (totals[actionName] || 0) + reduction;
        totalReduction += reduction;
    });

    const sorted = Object.entries(totals).sort((a, b) => b[1] - a[1]);

    bestActionEl.textContent = sorted.length ? sorted[0][0] : "기록 없음";
    bestReductionEl.textContent = sorted.length ? sorted[0][1].toFixed(3) + " kg" : "0 kg";
    totalEl.textContent = totalReduction.toFixed(3) + " kg";

    if (sorted.length === 0) {
        breakdownEl.textContent = "아직 기록이 없어요. 친환경 실천을 기록해 보세요!";
        feedbackEl.textContent = "기록이 쌓이면 나에게 효과적인 실천을 분석해 드릴게요.";
        return;
    }

    breakdownEl.innerHTML = sorted.map(([name, amount]) =>
        `<p>${name}: <strong>${amount.toFixed(3)} kg</strong></p>`
    ).join("");

    feedbackEl.textContent =
        `지금까지 ${sorted.length}가지 실천 유형을 기록했어요. 가장 효과적인 실천은 "${sorted[0][0]}"이에요!`;
}

function updateRewards(entries) {
    const count = entries.length;
    const total = entries.reduce(
        (sum, entry) => sum + (Number(entry.reduction) || 0),
        0
    );

    const level = Math.floor(count / 5) + 1;
    const levelNames = [
        "🌱 새싹",
        "🌿 초록이",
        "🌳 나무 지킴이",
        "🌎 지구 수호자",
        "♻️ 탄소 절약 마스터"
    ];
    const levelIndex = Math.min(level - 1, levelNames.length - 1);

    document.getElementById("rewardLevel").textContent =
        `${levelNames[levelIndex]} Lv.${level}`;
    document.getElementById("rewardCount").textContent = `${count}회`;
    document.getElementById("rewardReduction").textContent =
        `${total.toFixed(3)} kg`;

    const missions = [
        {
            name: "첫 실천 기록하기",
            description: "친환경 실천을 1회 기록하기",
            done: count >= 1
        },
        {
            name: "꾸준한 실천가",
            description: "친환경 실천을 5회 기록하기",
            done: count >= 5
        },
        {
            name: "실천 달인",
            description: "친환경 실천을 10회 기록하기",
            done: count >= 10
        },
        {
            name: "탄소 절약 시작",
            description: "누적 감축량 1kg 달성하기",
            done: total >= 1
        },
        {
            name: "지구 지킴이",
            description: "누적 감축량 10kg 달성하기",
            done: total >= 10
        }
    ];

    document.getElementById("missionList").innerHTML = missions.map(mission => `
        <p>${mission.done ? "✅" : "⬜"} ${mission.name}
        — ${mission.description}
        ${mission.done ? "<strong>달성!</strong>" : ""}</p>
    `).join("");

    const badges = [
        { name: "🌱 첫걸음", done: count >= 1 },
        { name: "🌿 꾸준한 실천", done: count >= 5 },
        { name: "🏆 실천 달인", done: count >= 10 },
        { name: "♻️ 탄소 절약가", done: total >= 1 },
        { name: "🌎 지구 수호자", done: total >= 10 }
    ];

    const earned = badges.filter(badge => badge.done);

    document.getElementById("badgeList").innerHTML = earned.length
        ? earned.map(badge => `<span style="display:inline-block; background:#e7eee6; padding:8px 12px; border-radius:12px; margin:4px;">${badge.name}</span>`).join("")
        : "아직 획득한 배지가 없어요. 첫 실천을 기록해 보세요!";
}

function renderEntries() {
    const entries = loadEntries();
renderCharts(entries);    
updateGoalProgress();
updatePersonalAnalysis(entries);
    updateRewards(entries);
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
    const countrySelect = document.getElementById("globalCountry");
    const trendSelect = document.getElementById("globalTrendCountry");
    const worldSummary = document.getElementById("globalWorldSummary");

    let totalChart;
    let perCapitaChart;
    let trendChart;
    let worldChart;

    async function getData(url) {
        const response = await fetch(url);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "데이터를 불러오지 못했습니다.");
        }
        return data.records;
    }

    function countryName(country) {
        const option = [...countrySelect.options].find(o => o.value === country);
        return option ? option.textContent : country;
    }

    async function render() {
        status.textContent = "데이터를 불러오는 중...";
        try {
            const year = Number(yearSelect.value);
            const selectedCountries = [...countrySelect.selectedOptions].map(o => o.value);
            const yearData = await getData("/api/global-data?year=" + year);
            const all = await getData("/api/global-data");

            const current = selectedCountries.map(country =>
                yearData.find(row => row.country === country)
            ).filter(Boolean);

            if (!current.length) {
                throw new Error("선택한 국가의 해당 연도 데이터가 없습니다.");
            }

            const labels = current.map(row => row.country_ko);
            const colors = ["#d9825b", "#4f7cac", "#7aa874", "#8b78b8", "#d6a84f", "#559e9b", "#bb779b", "#8b8b8b"];

            if (totalChart) totalChart.destroy();
            if (perCapitaChart) perCapitaChart.destroy();
            if (trendChart) trendChart.destroy();
            if (worldChart) worldChart.destroy();

            totalChart = new Chart(document.getElementById("globalTotalChart"), {
                type: "bar",
                data: {
                    labels,
                    datasets: [{
                        label: "총 CO₂ 배출량 (백만 톤)",
                        data: current.map(row => row.co2_million_tonnes),
                        backgroundColor: current.map((_, i) => colors[i % colors.length])
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
                        backgroundColor: current.map((_, i) => colors[i % colors.length])
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });

            const trendCountry = trendSelect.value;
            const trendRows = all.filter(row => row.country === trendCountry);
            const trendLabels = [...new Set(trendRows.map(row => row.year))].sort((a, b) => a - b);

            trendChart = new Chart(document.getElementById("globalTrendChart"), {
                type: "line",
                data: {
                    labels: trendLabels,
                    datasets: [{
                        label: countryName(trendCountry) + " CO₂ 배출량",
                        data: trendLabels.map(y => {
                            const row = trendRows.find(r => r.year === y);
                            return row ? row.co2_million_tonnes : null;
                        }),
                        borderColor: "#d9825b",
                        backgroundColor: "#d9825b",
                        tension: 0.2,
                        spanGaps: false
                    }]
                },
                options: {
                    responsive: true,
                    interaction: { mode: "index", intersect: false },
                    scales: { y: { beginAtZero: true } }
                }
            });

            const worldRows = all.filter(row => row.country === "World");
            const worldLabels = worldRows.map(row => row.year);
            worldChart = new Chart(document.getElementById("globalWorldChart"), {
                type: "line",
                data: {
                    labels: worldLabels,
                    datasets: [{
                        label: "세계 CO₂ 배출량 (백만 톤)",
                        data: worldRows.map(row => row.co2_million_tonnes),
                        borderColor: "#4f7cac",
                        backgroundColor: "rgba(79,124,172,0.15)",
                        fill: true,
                        tension: 0.2
                    }]
                },
                options: {
                    responsive: true,
                    interaction: { mode: "index", intersect: false },
                    scales: { y: { beginAtZero: true } }
                }
            });

            const worldCurrent = worldRows.find(row => row.year === year);
            if (worldCurrent) {
                worldSummary.textContent = year + "년 세계 CO₂ 배출량은 약 " +
                    Math.round(worldCurrent.co2_million_tonnes).toLocaleString("ko-KR") +
                    "백만 톤입니다.";
            }

            status.textContent = year + "년 데이터 · 선택 국가 " +
                current.length + "개 · 단위: 백만 톤 CO₂ / 톤 CO₂/명";
        } catch (error) {
            status.textContent = "데이터를 불러오지 못했어요: " + error.message;
        }
    }

    yearSelect.addEventListener("change", render);
    countrySelect.addEventListener("change", render);
    trendSelect.addEventListener("change", render);
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
  <h2>🌏 국가별·세계 탄소 배출량 비교</h2>
  <p>한국의 탄소 배출량은 시간이 지나면서 어떻게 달라졌을까요? 국가와 연도를 선택해 직접 비교해 보세요.</p>
  <p style="font-size:13px;color:#65746a;">Our World in Data 공개 자료 · 1990~2024년</p>

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

  <div style="margin-top:16px;">
    <label for="globalCountry">비교할 국가 (여러 개 선택 가능)</label><br>
    <select id="globalCountry" multiple size="7" style="width:100%;max-width:420px;padding:8px;">
      <option value="South Korea" selected>한국</option>
      <option value="United States" selected>미국</option>
      <option value="China" selected>중국</option>
      <option value="Japan" selected>일본</option>
      <option value="World">세계</option>
      <option value="India">인도</option>
      <option value="United Kingdom">영국</option>
      <option value="Germany">독일</option>
      <option value="France">프랑스</option>
      <option value="Canada">캐나다</option>
      <option value="Australia">호주</option>
      <option value="Brazil">브라질</option>
      <option value="Russia">러시아</option>
      <option value="Indonesia">인도네시아</option>
      <option value="Italy">이탈리아</option>
      <option value="Spain">스페인</option>
      <option value="Mexico">멕시코</option>
      <option value="South Africa">남아프리카공화국</option>
      <option value="Saudi Arabia">사우디아라비아</option>
      <option value="Türkiye">튀르키예</option>
    </select>
    <p style="font-size:12px;color:#65746a;">컴퓨터에서는 Ctrl 또는 Command 키를 누른 채 여러 국가를 선택할 수 있어요.</p>
  </div>

  <p id="globalCo2Status" role="status">데이터를 불러오는 중...</p>
  <h3>선택 국가의 총 CO₂ 배출량 (백만 톤)</h3>
  <canvas id="globalTotalChart"></canvas>
  <h3 style="margin-top:28px;">선택 국가의 1인당 CO₂ 배출량 (톤/명)</h3>
  <canvas id="globalPerCapitaChart"></canvas>

  <div style="margin-top:28px;">
    <label for="globalTrendCountry">연도별 변화 확인 국가</label>
    <select id="globalTrendCountry">
      <option value="South Korea" selected>한국</option>
      <option value="United States">미국</option>
      <option value="China">중국</option>
      <option value="Japan">일본</option>
      <option value="World">세계</option>
      <option value="India">인도</option>
      <option value="United Kingdom">영국</option>
      <option value="Germany">독일</option>
      <option value="France">프랑스</option>
      <option value="Canada">캐나다</option>
      <option value="Australia">호주</option>
      <option value="Brazil">브라질</option>
      <option value="Russia">러시아</option>
      <option value="Indonesia">인도네시아</option>
      <option value="Italy">이탈리아</option>
      <option value="Spain">스페인</option>
      <option value="Mexico">멕시코</option>
    </select>
  </div>
  <h3 style="margin-top:18px;">국가별 연도별 배출량 변화 (백만 톤)</h3>
  <canvas id="globalTrendChart"></canvas>

  <h3 style="margin-top:28px;">🌍 세계 전체 CO₂ 배출 추세</h3>
  <p id="globalWorldSummary">세계 데이터를 불러오는 중...</p>
  <canvas id="globalWorldChart"></canvas>

  <p style="font-size:12px;color:#65746a;margin-top:18px;">
    출처: Our World in Data, CO₂ emissions. 총배출량과 1인당 배출량은 서로 다른 지표입니다.
  </p>
</section>

<footer>Carbon Diary · 지속 가능한 일상을 위한 작은 실천</footer>
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




@app.route("/api/global-data")
def global_data():
    import pandas as pd

    data_path = os.path.join(
        os.path.dirname(__file__), "global_co2_extended.csv"
    )

    if not os.path.exists(data_path):
        return jsonify({"error": "탄소 배출량 데이터 파일을 찾을 수 없습니다."}), 500

    country_names = {
        "World": "세계",
        "South Korea": "한국",
        "United States": "미국",
        "China": "중국",
        "Japan": "일본",
        "United Kingdom": "영국",
        "Germany": "독일",
        "France": "프랑스",
        "India": "인도",
        "Canada": "캐나다",
        "Australia": "호주",
        "Brazil": "브라질",
        "Russia": "러시아",
        "Indonesia": "인도네시아",
        "Italy": "이탈리아",
        "Spain": "스페인",
        "Mexico": "멕시코",
        "South Africa": "남아프리카공화국",
        "Saudi Arabia": "사우디아라비아",
        "Türkiye": "튀르키예",
    }

    try:
        df = pd.read_csv(data_path)
        selected = request.args.get("country", "").strip()
        year = request.args.get("year", type=int)

        available_countries = set(df["country_en"].dropna().unique())

        if selected and selected not in available_countries:
            return jsonify({"error": "데이터에 없는 국가입니다."}), 400

        if year is not None and not 1990 <= year <= 2024:
            return jsonify({"error": "연도는 1990~2024년 사이여야 합니다."}), 400

        if selected:
            df = df[df["country_en"] == selected]

        if year is not None:
            df = df[df["year"] == year]

        df = df.sort_values(["year", "country_en"])

        records = []
        for _, row in df.iterrows():
            country = row["country_en"]
            per_capita = row["co2_per_capita_tonnes"]

            records.append({
                "country": country,
                "country_ko": country_names.get(country, country),
                "year": int(row["year"]),
                "co2_million_tonnes": round(float(row["co2_million_tonnes"]), 3),
                "co2_per_capita_tonnes": (
                    round(float(per_capita), 3)
                    if pd.notna(per_capita) else None
                ),
            })

        return jsonify({
            "source": "Our World in Data — CO₂ emissions",
            "unit_total": "백만 톤 CO₂",
            "unit_per_capita": "톤 CO₂/명",
            "records": records,
        })

    except (OSError, ValueError, KeyError) as error:
        return jsonify({"error": f"데이터 처리 중 오류가 발생했습니다: {error}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
