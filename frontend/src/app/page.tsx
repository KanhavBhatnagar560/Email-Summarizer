import DailyDigest from "./DailyDigest";

export default function Home() {
  return (
    
    <main style={{ maxWidth: 800, margin: "0 auto", padding: "2rem" }}>
      <h1>Welcome to the Email Summarizer</h1>
      <p>This application summarizes your daily Gmail digest.</p>
      <p>
        Click the button below to get your daily email summary.
      </p>
      <DailyDigest />
    </main>
  );
}
