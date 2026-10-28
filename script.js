// Append this to the bottom of script.js
document.getElementById("analyze-button").onclick{
    const analyzeButton = document.getElementById("analyze-button");
    
    if (analyzeButton) {
        analyzeButton.addEventListener("click", async () => {
            const resultDiv = document.getElementById("analysis-result");
            // Assuming your HTML has a file picker element with an id matching "image-input" or similar
            const fileInput = document.querySelector('input[type="file"]') || document.getElementById("image-upload");
            
            if (resultDiv) {
                resultDiv.innerHTML = "Analyzing construction site safety...";
            }

            if (!fileInput || !fileInput.files[0]) {
                if (resultDiv) {
                    resultDiv.innerHTML = '<span style="color: orange;">Please select an image file first.</span>';
                }
                return;
            }

            // Must use FormData since the backend reads a multi-part form file boundary
            const formData = new FormData();
            formData.append("image", fileInput.files[0]);

            try {
                const response = await fetch("http://127.0.0", {
                    method: "POST",
                    body: formData // Browser handles Content-Type boundaries automatically
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || Server status: ${response.status});
                }

                const data = await response.json();
                if (resultDiv) {
                    // Render the report text cleanly returned from Gemini
                    resultDiv.innerHTML = `
                        <h3>Analysis Report</h3>
                        <p style="white-space: pre-wrap;">${data.report || JSON.stringify(data)}</p>
                        <small style="color: gray; display: block; margin-top: 10px;">${data.notice || ''}</small>
                    `;
                }
            } catch (error) {
                console.error("Error connecting to safety endpoint:", error);
                if (resultDiv) {
                    resultDiv.innerHTML = <span style="color: red;">Error: ${error.message}</span>;
                }
            }
        });
    }
});