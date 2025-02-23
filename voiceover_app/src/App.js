import { useState } from "react";
import axios from "axios";

function App() {
    const [text, setText] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const response = await axios.post(
                "http://127.0.0.1:5000/synthesize",
                { text },
                { responseType: "blob" } // Important for MP3 files
            );
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const a = document.createElement("a");
            a.href = url;
            a.download = "voiceover.mp3";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } catch (error) {
            console.error("Error generating voiceover:", error);
        }
        setLoading(false);
    };

    return (
        <div style={{ padding: 20 }}>
            <h1>AI Voiceover Generator</h1>
            <textarea
                rows="4"
                cols="50"
                placeholder="Enter your script..."
                value={text}
                onChange={(e) => setText(e.target.value)}
            />
            <br />
            <button onClick={handleSubmit} disabled={loading}>
                {loading ? "Generating..." : "Generate Voiceover"}
            </button>
        </div>
    );
}

export default App;
