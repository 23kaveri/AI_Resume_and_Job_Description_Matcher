document.getElementById("compareForm").addEventListener("submit", async (e) => {
  e.preventDefault(); // prevent form reload

  const resume = document.getElementById("resume").files[0];
  const job = document.getElementById("job").files[0];

  if (!resume || !job) {
    alert("Please choose both files before comparing!");
    return;
  }

  const formData = new FormData();
  formData.append("resume", resume);
  formData.append("job", job);

  try {
    const response = await fetch("/compare", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (data.error) {
      document.getElementById("result").innerHTML = <p style="color:red;">${data.error}</p>;
    } else {
      document.getElementById("result").innerHTML = `
        <h3>Results:</h3>
        <p><b>Similarity Score:</b> ${data.similarity_score}%</p>
        <p><b>Resume Skills:</b> ${data.resume_skills.join(", ")}</p>
        <p><b>Job Skills:</b> ${data.job_skills.join(", ")}</p>
        <p><b>Missing Skills:</b> ${data.missing_skills.join(", ") || "None"}</p>
        <p><b>Rank:</b> ${data.rank}</p>
      `;
    }
  } catch (err) {
    document.getElementById("result").innerHTML =
      <p style="color:red;">Error connecting to server.</p>;
  }
});