import { useState } from "react";

// ⚠️ هتغير ده بعد النشر على Railway
const BASE_URL = import.meta.env.VITE_API_URL;

type Article = {
    id: number;
    title: string;
    predicted: string;
    confidence: number;
    message?: string;
};

export default function App() {

    const [reviewer, setReviewer] = useState("");
    const [article, setArticle] = useState<Article | null>(null);
    const [loading, setLoading] = useState(false);

    async function loadArticle() {
        try {
            setLoading(true);

            const res = await fetch(
                `${BASE_URL}/news/review?reviewer=${reviewer}`
            );

            const data = await res.json();
            setArticle(data);

        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    async function submit(category: string) {

        if (!article) return;

        await fetch(`${BASE_URL}/news/review`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: article.id,
                category,
                reviewer
            })
        });

        loadArticle();
    }

    if (!reviewer) {
        return (
            <div style={{ padding: 40 }}>
                <h2>Enter your name</h2>

                <input
                    placeholder="Reviewer name"
                    onChange={(e) => setReviewer(e.target.value)}
                />

                <button onClick={loadArticle}>
                    Start
                </button>
            </div>
        );
    }

    if (loading) {
        return <h2>Loading...</h2>;
    }

    if (!article || article.message) {
        return <h2>No articles left 🎉</h2>;
    }

    return (
        <div style={{ padding: 40 }}>

            <h2>{article.title}</h2>

            <p>
                Predicted: {article.predicted}
                ({article.confidence})
            </p>

            <button onClick={() => submit("رياضة")}>رياضة</button>
            <button onClick={() => submit("سياسة")}>سياسة</button>
            <button onClick={() => submit("فن")}>فن</button>
            <button onClick={() => submit("اجتماعية")}>اجتماعية</button>

        </div>
    );
}