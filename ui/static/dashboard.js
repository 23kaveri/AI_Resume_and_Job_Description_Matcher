// MAIN UPLOAD HANDLER
document.getElementById("uploadForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = document.getElementById("uploadForm");
    const f = new FormData(form);

    // SAFETY CHECK
    if (!f.get("resume") || !f.get("job_pdf")) {
        alert("❌ Please select both files first!");
        return;
    }

    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    submitBtn.textContent = "Analyzing…";

    try {
        const res = await fetch("/compare", { method: "POST", body: f });
        const data = await res.json();

        if (!res.ok) {
            alert(data.error || "Server error");
            return;
        }

        updateDashboard(data);

    } catch (err) {
        console.error(err);
        alert("Network error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Compare Now";
    }
});


// -------------------------------
// UPDATE DASHBOARD UI
// -------------------------------
function updateDashboard(data) {
    const results = data.results || [];

    // ⭐ SAVE FOR REPORTS PAGE
    localStorage.setItem("ai_saved_scans", JSON.stringify(results));

    // STATS
    document.getElementById("statTotal").textContent = results.length || "—";

    const best = results.length ? Math.max(...results.map(r => r.match_score)) : 0;
    const avg = results.length ? (results.reduce((s, r) => s + r.match_score, 0) / results.length).toFixed(2) : "—";
    const matchedSkills = results.reduce((s, r) => s + (r.matching_skills?.length || 0), 0);

    document.getElementById("statBest").textContent = best ? best + "%" : "—";
    document.getElementById("statAvg").textContent = avg ? avg + "%" : "—";
    document.getElementById("statSkills").textContent = matchedSkills;

    // SUMMARY
    document.getElementById("topSummary").textContent =
        `Top match: ${data.top_match} | Compared ${data.total_jobs_compared} jobs`;

    // TABLE + CHART
    fillResultsTable(results);
    drawBucketChart(results);
}


// -------------------------------
// TABLE FUNCTION (NOW SHOWS VALIDITY)
// -------------------------------
function fillResultsTable(results) {
    const tbody = document.querySelector("#resultsTable tbody");
    tbody.innerHTML = "";

    results.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${r.job_title}</td>
            <td class="match">${r.match_score}%</td>
            <td>${(r.matching_skills || []).join(", ")}</td>
            <td class="missing">${(r.missing_skills || []).join(", ") || "—"}</td>
            <td>${r.company || "Not Provided"}</td>
            <td style="color:#00ffa6">${r.validity || "Not Mentioned"}</td>  <!-- 🔥 Added -->
        `;
        tbody.appendChild(tr);
    });
}



// -------------------------------
// BAR CHART (NEON GRADIENT)
// -------------------------------
let bucketChart = null;

function drawBucketChart(results) {
    const buckets = Array(10).fill(0);

    results.forEach(job => {
        const idx = Math.min(Math.floor(job.match_score / 10), 9);
        buckets[idx]++;
    });

    const ctx = document.getElementById("matchChart").getContext("2d");
    if (bucketChart) bucketChart.destroy();

    bucketChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: [
                "0–10%", "10–20%", "20–30%", "30–40%", "40–50%",
                "50–60%", "60–70%", "70–80%", "80–90%", "90–100%"
            ],
            datasets: [{
                label: "Job Match Distribution",
                data: buckets,
                backgroundColor: function (context) {
                    const chart = context.chart;
                    const { ctx } = chart;

                    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                    gradient.addColorStop(0, "rgba(0,255,255,0.9)");
                    gradient.addColorStop(0.5, "rgba(0,180,255,0.9)");
                    gradient.addColorStop(1, "rgba(150,0,255,0.95)");
                    return gradient;
                },
                borderRadius: 14,
                barPercentage: 0.9,
                categoryPercentage: 1,
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: "#d9d9ff" },
                    grid: { color: "rgba(255,255,255,0.08)" }
                },
                x: {
                    ticks: { color: "#d9d9ff" },
                    grid: { color: "rgba(255,255,255,0.04)" }
                }
            }
        }
    });
}
