document.getElementById("uploadForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    console.log("📤 Upload started…");

    const formData = new FormData();
    formData.append("resume", document.getElementById("resume").files[0]);
    formData.append("job_pdf", document.getElementById("job_pdf").files[0]);

    // Show loading
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("result").classList.add("hidden");

    try {
        const response = await fetch("/compare", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();
        console.log("📥 SERVER RESPONSE:", data);

        if (data.error) {
            alert("❌ ERROR: " + data.error);
            return;
        }

        // Hide loader, show results
        document.getElementById("loading").classList.add("hidden");
        document.getElementById("result").classList.remove("hidden");

        // Summary
        document.getElementById("summary").innerText =
            `Top Match: ${data.top_match} | Compared ${data.total_jobs_compared} jobs`;

        // Fill Table
        const tbody = document.querySelector("#resultsTable tbody");
        tbody.innerHTML = "";

        data.results.forEach(job => {
            tbody.innerHTML += `
                <tr>
                    <td>${job.job_title}</td>
                    <td>${job.match_score}%</td>
                    <td>${job.matching_skills.join(", ")}</td>
                    <td>${job.missing_skills.join(", ")}</td>
                    <td>${job.company}</td>
                </tr>
            `;
        });

        // Match Score Distribution Chart
        const buckets = Array(10).fill(0);
        data.results.forEach(job => {
            const idx = Math.min(Math.floor(job.match_score / 10), 9);
            buckets[idx]++;
        });

        const ctx = document.getElementById("matchChart").getContext("2d");

        new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["0–10%", "10–20%", "20–30%", "30–40%", "40–50%", "50–60%", "60–70%", "70–80%", "80–90%", "90–100%"],
                datasets: [{
                    label: "Job Match Distribution",
                    data: buckets,
                    backgroundColor: "#4e54c8"
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });

    } catch (err) {
        alert("❌ SERVER ERROR — Check the Terminal");
        console.error(err);
    }
});