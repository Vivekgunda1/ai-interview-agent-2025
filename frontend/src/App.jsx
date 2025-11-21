import { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [stage, setStage] = useState('start');
  const [history, setHistory] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const startInterview = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.target);

    try {
      const res = await axios.post('http://127.0.0.1:8000/start-interview', formData);
      setSessionId(res.data.session_id);
      setHistory([{ speaker: 'AI', text: res.data.message }]);
      setStage('interviewing');
    } catch (err) {
      alert("Error: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  // ← THIS IS THE ONLY sendAnswer FUNCTION YOU NEED (uses FormData → fixes 422 error)
  const sendAnswer = async () => {
    if (!answer.trim() || loading) return;

    setHistory(prev => [...prev, { speaker: 'You', text: answer }]);
    setLoading(true);
    const userAnswer = answer;
    setAnswer('');

    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('user_answer', userAnswer);

      const res = await axios.post('http://127.0.0.1:8000/answer', formData);
      setHistory(prev => [...prev, { speaker: 'AI', text: res.data.reply }]);
    } catch (err) {
      setHistory(prev => [...prev, { speaker: 'AI', text: 'Error: ' + (err.message || 'Server issue') }]);
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <header>
        <h1> AI Interview Agent</h1>
      </header>

      {stage === 'start' && (
        <div className="form">
          <form onSubmit={startInterview}>
            <input name="candidate_name" placeholder="Your Name" required />
            <input name="job_role" placeholder="Job Role (e.g. .NET Developer)" required />
            <input type="file" name="resume" accept=".pdf" required />
            <button type="submit" disabled={loading}>
              {loading ? 'Starting...' : 'Start Interview'}
            </button>
          </form>
        </div>
      )}

      {stage === 'interviewing' && (
        <div className="chat">
          <div className="messages">
            {history.map((msg, i) => (
              <div key={i} className={msg.speaker === 'You' ? 'user' : 'ai'}>
                <strong>{msg.speaker}:</strong> {msg.text}
              </div>
            ))}
            {loading && <div className="ai"><strong>Interviewer:</strong> Thinking...</div>}
          </div>

          <div className="input-area">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer (press Enter to send)"
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendAnswer())}
            />
            <button onClick={sendAnswer} disabled={loading}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;