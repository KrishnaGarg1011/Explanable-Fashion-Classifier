function uploadImage() {
    const input = document.getElementById("imageInput");
    const file = input.files[0];

    if (!file) {
        alert("Please select an image first!");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    // Replace with your backend URL if deployed
    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("result").innerText = 
            `Label: ${data.label}\nConfidence: ${data.confidence}\nExplanation: ${data.explanation}`;
    })
    .catch(error => {
        console.error("Error uploading image:", error);
    });
}
