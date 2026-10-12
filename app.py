import os
import socket
import json
import urllib.request
from urllib.parse import urlparse
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server & IP Lookup Tool</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body class="bg-slate-50 text-slate-800 font-sans min-h-screen flex flex-col justify-between">
    <header class="bg-white border-b border-slate-200 py-4 px-6 shadow-sm">
        <div class="max-w-5xl mx-auto flex justify-between items-center">
            <h1 class="text-xl font-bold text-indigo-600 tracking-tight">📍 NetInspect</h1>
            <span class="text-xs bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full font-medium">Web Utility v1.0</span>
        </div>
    </header>

    <main class="max-w-3xl w-full mx-auto p-6 flex-grow flex flex-col justify-center my-8">
        <div class="text-center mb-8">
            <h2 class="text-3xl font-extrabold text-slate-900 mb-2">Server Infrastructure Lookup</h2>
            <p class="text-slate-500">Convert a website URL into its core IP address and hosting provider data.</p>
        </div>

        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-6">
            <form id="lookup-form" class="flex flex-col sm:flex-row gap-3">
                <input
                    type="text"
                    id="url-input"
                    name="url"
                    required
                    placeholder="Enter website domain (e.g., github.com)"
                    class="flex-grow px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-base"
                >
                <button
                    type="submit"
                    class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition duration-150 cursor-pointer shadow-sm active:scale-[0.98]"
                >
                    Inspect Server
                </button>
            </form>
        </div>

        <div id="loading" class="hidden text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent mb-2"></div>
            <p class="text-slate-500 text-sm">Resolving host and querying data infrastructure...</p>
        </div>

        <div id="error-card" class="hidden bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl mb-6 text-sm"></div>

        <div id="results" class="hidden bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition-all duration-300">
            <div class="bg-slate-900 text-white p-4 px-6 flex justify-between items-center">
                <div>
                    <span class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Target Domain</span>
                    <h3 id="res-domain" class="text-lg font-bold text-indigo-400">---</h3>
                </div>
                <div class="text-right">
                    <span class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Resolved IP</span>
                    <p id="res-ip" class="font-mono text-sm font-bold text-emerald-400">0.0.0.0</p>
                </div>
            </div>

            <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Hosting & Network</h4>
                    <div class="space-y-3">
                        <div>
                            <span class="text-xs text-slate-400 block">ISP / Hosting Provider</span>
                            <span id="res-isp" class="font-semibold text-slate-800">---</span>
                        </div>
                        <div>
                            <span class="text-xs text-slate-400 block">Organization Owner</span>
                            <span id="res-org" class="font-semibold text-slate-800">---</span>
                        </div>
                        <div>
                            <span class="text-xs text-slate-400 block">Autonomous System (ASN)</span>
                            <span id="res-as" class="font-mono text-xs bg-slate-100 px-2 py-0.5 rounded text-slate-700">---</span>
                        </div>
                    </div>
                </div>

                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Server Location</h4>
                    <div class="space-y-3">
                        <div>
                            <span class="text-xs text-slate-400 block">Country</span>
                            <span id="res-country" class="font-semibold text-slate-800">---</span>
                        </div>
                        <div>
                            <span class="text-xs text-slate-400 block">Region / City</span>
                            <span id="res-location" class="font-semibold text-slate-800">---</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        &copy; 2026 NetInspect Utility Framework. Ready for commercial database integration.
    </footer>

    <script>
        document.getElementById('lookup-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const urlInput = document.getElementById('url-input').value;
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            const errorCard = document.getElementById('error-card');

            loading.classList.remove('hidden');
            results.classList.add('hidden');
            errorCard.classList.add('hidden');

            try {
                const response = await fetch('/api/lookup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: urlInput })
                });

                const data = await response.json();

                if (data.status === 'success') {
                    document.getElementById('res-domain').textContent = data.domain;
                    document.getElementById('res-ip').textContent = data.ip;
                    document.getElementById('res-isp').textContent = data.isp || 'Unknown';
                    document.getElementById('res-org').textContent = data.org || 'Unknown';
                    document.getElementById('res-as').textContent = data.as || 'Unknown';
                    document.getElementById('res-country').textContent = data.country || 'Unknown';
                    document.getElementById('res-location').textContent = [data.city, data.region].filter(Boolean).join(', ') || 'Unknown';

                    results.classList.remove('hidden');
                } else {
                    errorCard.textContent = data.message || 'Lookup failure.';
                    errorCard.classList.remove('hidden');
                }
            } catch (err) {
                errorCard.textContent = 'Failed to connect to the backend lookup server.';
                errorCard.classList.remove('hidden');
            } finally {
                loading.classList.add('hidden');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/lookup', methods=['POST'])
def lookup_api():
    try:
        req_data = request.get_json(silent=True) or {}
        raw_url = (req_data.get('url') or '').strip()

        if not raw_url:
            return jsonify({'status': 'error', 'message': 'No domain or URL provided.'}), 400

        if not raw_url.startswith(('http://', 'https://')):
            raw_url = 'http://' + raw_url

        parsed = urlparse(raw_url)
        domain = parsed.netloc or parsed.path

        if not domain:
            return jsonify({'status': 'error', 'message': 'Invalid URL format.'}), 400

        ip_address = socket.gethostbyname(domain)

        api_url = f'https://ipapi.co/{ip_address}/json/'
        with urllib.request.urlopen(api_url, timeout=10) as response:
            server_data = json.loads(response.read().decode())

        if server_data.get('error'):
            return jsonify({'status': 'error', 'message': server_data.get('reason', 'IP metadata fetch failed.')})

        return jsonify({
            'status': 'success',
            'domain': domain,
            'ip': ip_address,
            'isp': server_data.get('org') or server_data.get('isp'),
            'org': server_data.get('org'),
            'as': server_data.get('asn') or server_data.get('as'),
            'country': server_data.get('country_name') or server_data.get('country'),
            'region': server_data.get('region'),
            'city': server_data.get('city')
        })

    except socket.gaierror:
        return jsonify({'status': 'error', 'message': 'Could not resolve domain name. Check spelling.'})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
