import streamlit as st
import pandas as pd
import googleapiclient.discovery
import re
from transformers import pipeline
import plotly.express as px

# -----------------------------
# ⚙️ Load 3-class Sentiment Model
# -----------------------------
@st.cache_resource
def load_model():
    # CardifNLP Twitter-RoBERTa Sentiment (POSITIVE / NEUTRAL / NEGATIVE)
    return pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

sentiment_model = load_model()

# -----------------------------
# 🎥 Fetch YouTube Comments
# -----------------------------
def fetch_comments(video_url, api_key, max_results=50):
    video_id_match = re.search(r"v=([a-zA-Z0-9_-]+)", video_url)
    if not video_id_match:
        st.error("⚠️ Invalid YouTube video URL!")
        return []

    video_id = video_id_match.group(1)
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText"
    )
    response = request.execute()

    comments = []
    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(comment)
    return comments

# -----------------------------
# 🧠 Predict Sentiment
# -----------------------------
label_map = {"LABEL_0": "Negative", "LABEL_1": "Neutral", "LABEL_2": "Positive"}

def analyze_sentiments(comments):
    results = []
    for c in comments:
        try:
            prediction = sentiment_model(c[:512])[0]  # truncate for BERT
            label = label_map.get(prediction["label"], "Neutral")
            score = round(prediction["score"] * 100, 2)
            results.append({"Comment": c, "Sentiment": label, "Confidence (%)": score})
        except:
            results.append({"Comment": c, "Sentiment": "Neutral", "Confidence (%)": 0})
    return pd.DataFrame(results)

# -----------------------------
# 🌐 Streamlit UI
# -----------------------------
st.set_page_config(page_title="🎭 YouTube Sentiment Analyzer", page_icon="🎬", layout="wide")

st.title("🎬 YouTube Comments Sentiment Analysis (3-Class)")
st.markdown("""
Enter a **YouTube video URL** and **YouTube API Key** to fetch comments.  
The app will classify comments as **Positive**, **Neutral**, or **Negative** and show visual insights.
""")

api_key = st.text_input("🔑 Enter YouTube API Key:", type="password")
video_url = st.text_input("📺 Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=example")

if st.button("🚀 Analyze Comments"):
    if not api_key or not video_url:
        st.warning("Please enter both the API key and video URL!")
    else:
        with st.spinner("Fetching and analyzing comments..."):
            comments = fetch_comments(video_url, api_key)
            if not comments:
                st.stop()

            df = analyze_sentiments(comments)

            # Show Data
            st.subheader("🧾 Analyzed Comments")
            st.dataframe(df, use_container_width=True)

            # -----------------------------
            # 📊 Charts and Stats
            # -----------------------------
            sentiment_counts = df["Sentiment"].value_counts().reset_index()
            sentiment_counts.columns = ["Sentiment", "Count"]
            total = sentiment_counts["Count"].sum()
            sentiment_counts["Percentage"] = (sentiment_counts["Count"] / total * 100).round(2)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Sentiment Bar Chart")
                fig_bar = px.bar(
                    sentiment_counts,
                    x="Sentiment",
                    y="Count",
                    color="Sentiment",
                    text="Percentage",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                st.subheader("🥧 Sentiment Pie Chart")
                fig_pie = px.pie(
                    sentiment_counts,
                    values="Count",
                    names="Sentiment",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            # -----------------------------
            # 📊 Summary Section
            # -----------------------------
            st.markdown("### 📊 Sentiment Summary")
            for _, row in sentiment_counts.iterrows():
                st.write(f"- **{row['Sentiment']}**: {row['Count']} comments ({row['Percentage']}%)")

            # -----------------------------
            # 💾 CSV Download
            # -----------------------------
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="💾 Download Results as CSV",
                data=csv_data,
                file_name="youtube_sentiment_results.csv",
                mime="text/csv"
            )

            st.success("✅ Analysis complete!")

st.markdown("---")
st.caption("Built with ❤️ by Jaddu Mohan Kishore")
