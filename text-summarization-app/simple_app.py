from flask import Flask, render_template_string, request, jsonify
import re

app = Flask(__name__)

# HTML template (everything in one file)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Text Summarizer</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        textarea { width: 100%; height: 200px; padding: 10px; border: 2px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        .result { background: #f8f9fa; padding: 20px; margin-top: 20px; border-radius: 5px; border-left: 4px solid #007bff; }
        .stats { background: #e7f3ff; padding: 15px; margin-top: 10px; border-radius: 5px; }
        h1 { color: #333; text-align: center; }
        .row { display: flex; gap: 20px; }
        .col { flex: 1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Text Summarization Tool</h1>
        
        <div class="row">
            <div class="col">
                <h3>Input Text</h3>
                <textarea id="inputText" placeholder="Paste your article or text here..."></textarea>
                <br><br>
                <button onclick="summarizeText()">Generate Summary</button>
                <button onclick="loadSample()" style="background: #28a745;">Load Sample</button>
            </div>
            
            <div class="col">
                <h3>Summary</h3>
                <div id="summary" class="result" style="min-height: 200px;">
                    Your summary will appear here...
                </div>
                <div id="stats" class="stats" style="display: none;"></div>
            </div>
        </div>
    </div>

    <script>
        function loadSample() {
            document.getElementById('inputText').value = `Artificial intelligence (AI) has emerged as one of the most transformative technologies of our time. From healthcare and finance to transportation and entertainment, AI is revolutionizing how we work and live.

Machine learning, a subset of AI, enables computers to learn from experience without being explicitly programmed. Companies like Google, Microsoft, and Amazon have invested billions in AI research, creating systems that understand speech, recognize images, and make complex decisions.

The healthcare industry has been particularly transformed by AI applications. Medical professionals now use AI-powered diagnostic tools to detect diseases earlier and more accurately. Deep learning algorithms can analyze medical images to identify cancer cells with precision that often exceeds human capabilities.

In the financial sector, AI has revolutionized fraud detection, algorithmic trading, and risk assessment. Banks use machine learning models to analyze transaction data in real-time, identifying suspicious patterns and preventing fraudulent activities.

However, the rapid advancement of AI also raises important ethical concerns. Issues such as job displacement, privacy protection, and algorithmic bias need careful consideration as we continue to develop and deploy AI systems.`;
        }
        
        async function summarizeText() {
            const text = document.getElementById('inputText').value.trim();
            if (!text) {
                alert('Please enter some text first!');
                return;
            }
            
            try {
                const response = await fetch('/summarize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('summary').innerHTML = '<div style="color: red;">Error: ' + data.error + '</div>';
                } else {
                    document.getElementById('summary').innerHTML = '<strong>Summary:</strong><br><br>' + data.summary;
                    document.getElementById('stats').innerHTML = 
                        'Original: ' + data.stats.original_words + ' words, ' + data.stats.original_sentences + ' sentences<br>' +
                        'Summary: ' + data.stats.summary_words + ' words, ' + data.stats.summary_sentences + ' sentences<br>' +
                        'Compression: ' + data.stats.compression + '%';
                    document.getElementById('stats').style.display = 'block';
                }
            } catch (error) {
                document.getElementById('summary').innerHTML = '<div style="color: red;">Error connecting to server</div>';
            }
        }
    </script>
</body>
</html>
'''

# Simple summarizer function
def simple_summarize(text, max_sentences=3):
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text
    
    # Simple scoring: count important words
    stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'}
    words = re.findall(r'\b\w+\b', text.lower())
    words = [w for w in words if w not in stop_words and len(w) > 2]
    
    word_count = {}
    for word in words:
        word_count[word] = word_count.get(word, 0) + 1
    
    # Score sentences
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        sentence_words = re.findall(r'\b\w+\b', sentence.lower())
        score = sum(word_count.get(word, 0) for word in sentence_words if word not in stop_words)
        sentence_scores.append((score, i, sentence))
    
    # Get top sentences
    sentence_scores.sort(reverse=True)
    top_sentences = sentence_scores[:max_sentences]
    top_sentences.sort(key=lambda x: x[1])  # Keep original order
    
    return '. '.join([s[2] for s in top_sentences]) + '.'

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if len(text.split()) < 10:
            return jsonify({'error': 'Please provide at least 10 words'})
        
        summary = simple_summarize(text)
        
        # Stats
        original_words = len(text.split())
        original_sentences = len(re.split(r'[.!?]+', text))
        summary_words = len(summary.split())
        summary_sentences = len(re.split(r'[.!?]+', summary))
        compression = round((summary_words / original_words) * 100, 1)
        
        return jsonify({
            'summary': summary,
            'stats': {
                'original_words': original_words,
                'original_sentences': original_sentences,
                'summary_words': summary_words,
                'summary_sentences': summary_sentences,
                'compression': compression
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("Starting Text Summarizer...")
    print("Open your browser to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)