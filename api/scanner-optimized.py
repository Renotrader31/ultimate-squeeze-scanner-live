from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import os
from datetime import datetime
import time
import concurrent.futures
from threading import Lock
import random

class handler(BaseHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        # Optimized ticker universe - focused on high-potential candidates
        self.ticker_universe = {
            'top_meme_stocks': [
                'GME', 'AMC', 'BBBY', 'SAVA', 'VXRT', 'CLOV', 'SPRT', 'IRNT', 
                'DWAC', 'PHUN', 'PROG', 'ATER', 'BBIG', 'MULN', 'EXPR', 'KOSS'
            ],
            'high_short_interest': [
                'BYND', 'PTON', 'ROKU', 'UPST', 'AFRM', 'HOOD', 'COIN', 'RIVN',
                'LCID', 'NKLA', 'PLUG', 'BLNK', 'QS', 'GOEV', 'RIDE', 'WKHS'
            ],
            'biotech_squeeze': [
                'BIIB', 'GILD', 'REGN', 'BMRN', 'ALNY', 'SRPT', 'IONS', 'ARWR',
                'EDIT', 'CRSP', 'NTLA', 'BEAM', 'BLUE', 'FOLD', 'RARE', 'KRYS'
            ],
            'small_cap_movers': [
                'SPCE', 'DKNG', 'PENN', 'FUBO', 'WISH', 'RBLX', 'PLTR', 'SNOW',
                'CRWD', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC', 'ZM', 'DOCN'
            ],
            'large_cap_samples': [
                'AAPL', 'TSLA', 'META', 'NFLX', 'NVDA', 'GOOGL', 'AMZN', 'MSFT'
            ]
        }
        
        # Flatten all tickers into master list
        self.master_ticker_list = []
        for category, tickers in self.ticker_universe.items():
            self.master_ticker_list.extend(tickers)
        
        # Remove duplicates while preserving order
        seen = set()
        self.master_ticker_list = [x for x in self.master_ticker_list if not (x in seen or seen.add(x))]
        
        self.scan_lock = Lock()
        self.scan_results_cache = {}
        self.last_scan_time = None
        
        # Performance tracking
        self.performance_stats = {
            'avg_ticker_time': 2.5,  # Average seconds per ticker
            'max_safe_batch_size': 20,  # Maximum safe batch size
            'timeout_threshold': 45  # Maximum scan time in seconds
        }
        
        super().__init__(*args, **kwargs)
    
    def calculate_optimal_scan_size(self, requested_size, timeout_limit=45):
        """Calculate optimal scan size based on performance metrics"""
        avg_time_per_ticker = self.performance_stats['avg_ticker_time']
        max_safe_size = int(timeout_limit / avg_time_per_ticker * 0.8)  # 80% safety margin
        
        optimal_size = min(requested_size, max_safe_size, self.performance_stats['max_safe_batch_size'])
        
        return {
            'optimal_size': optimal_size,
            'estimated_time': optimal_size * avg_time_per_ticker,
            'timeout_risk': 'low' if optimal_size <= 15 else 'medium' if optimal_size <= 25 else 'high',
            'recommended_min_score': 50 if optimal_size > 20 else 30 if optimal_size > 10 else 0
        }
    
    def get_fast_ortex_data(self, ticker, ortex_key, timeout=3):
        """Fast Ortex data retrieval with short timeout"""
        if not ortex_key:
            return None
            
        # Only try the known working endpoints for speed
        working_endpoints = [
            f'https://api.ortex.com/api/v1/stock/nasdaq/{ticker}/short_interest',
            f'https://api.ortex.com/api/v1/stock/nyse/{ticker}/short_interest',
        ]
        
        for url in working_endpoints:
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Ultimate-Squeeze-Scanner/2.0')
                req.add_header('Accept', 'application/json')
                req.add_header('Ortex-Api-Key', ortex_key)
                
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.getcode() == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            data = response.read().decode('utf-8')
                            try:
                                json_data = json.loads(data)
                                return self.process_ortex_json_fast(json_data)
                            except json.JSONDecodeError:
                                continue
                                
            except Exception:
                continue
        
        return None
    
    def process_ortex_json_fast(self, json_data):
        """Fast processing of Ortex JSON data"""
        processed = {
            'short_interest': None,
            'utilization': None,
            'cost_to_borrow': None,
            'days_to_cover': None,
            'data_quality': 'live_ortex',
            'source_endpoints': ['ortex_fast']
        }
        
        # Quick extraction of common fields
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, (int, float)):
                    key_lower = str(key).lower()
                    if 'short_interest' in key_lower or 'si' in key_lower:
                        processed['short_interest'] = value
                    elif 'utilization' in key_lower or 'util' in key_lower:
                        processed['utilization'] = value
                    elif 'cost_to_borrow' in key_lower or 'ctb' in key_lower:
                        processed['cost_to_borrow'] = value
                    elif 'days_to_cover' in key_lower or 'dtc' in key_lower:
                        processed['days_to_cover'] = value
        
        # Quick estimates for missing data
        if processed['short_interest'] and not processed['utilization']:
            processed['utilization'] = min(processed['short_interest'] * 3.5, 95)
        if processed['short_interest'] and not processed['days_to_cover']:
            processed['days_to_cover'] = max(processed['short_interest'] * 0.2, 0.8)
        if processed['short_interest'] and not processed['cost_to_borrow']:
            processed['cost_to_borrow'] = max(processed['short_interest'] * 0.4, 1.0)
            
        return processed
    
    def get_yahoo_price_data_fast(self, tickers, max_workers=15):
        """Optimized Yahoo Finance data with reduced workers to prevent timeouts"""
        price_data = {}
        
        def get_single_price_fast(ticker):
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0 (compatible; SqueezeScanner/1.0)')
                
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = json.loads(response.read())
                    
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        meta = result.get('meta', {})
                        
                        current_price = meta.get('regularMarketPrice', 0)
                        previous_close = meta.get('previousClose', 0)
                        volume = meta.get('regularMarketVolume', 0)
                        
                        price_change = current_price - previous_close if previous_close else 0
                        price_change_pct = (price_change / previous_close * 100) if previous_close else 0
                        
                        return {
                            'ticker': ticker,
                            'current_price': round(current_price, 2),
                            'price_change': round(price_change, 2),
                            'price_change_pct': round(price_change_pct, 2),
                            'volume': volume,
                            'success': True
                        }
                        
            except Exception as e:
                return {'ticker': ticker, 'success': False, 'error': str(e)}
        
        # Reduced thread pool size for stability
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {executor.submit(get_single_price_fast, ticker): ticker for ticker in tickers}
            
            for future in concurrent.futures.as_completed(future_to_ticker, timeout=30):
                try:
                    result = future.result(timeout=5)
                    if result and result.get('success'):
                        price_data[result['ticker']] = result
                except (concurrent.futures.TimeoutError, Exception):
                    # Skip failed tickers to prevent timeout
                    continue
        
        return price_data
    
    def generate_smart_mock_data(self, tickers):
        """Smart mock data generation with realistic profiles"""
        mock_data = {}
        
        # High-probability squeeze profiles
        squeeze_profiles = {
            'GME': {'si': 22.4, 'util': 89.2, 'ctb': 12.8, 'dtc': 4.1},
            'AMC': {'si': 18.7, 'util': 82.1, 'ctb': 8.9, 'dtc': 3.8},
            'SAVA': {'si': 35.2, 'util': 95.1, 'ctb': 45.8, 'dtc': 12.3},
            'VXRT': {'si': 28.9, 'util': 87.6, 'ctb': 18.2, 'dtc': 8.7},
            'BBBY': {'si': 42.1, 'util': 98.2, 'ctb': 78.5, 'dtc': 15.8},
            'BYND': {'si': 31.5, 'util': 91.7, 'ctb': 25.3, 'dtc': 9.2},
            'PTON': {'si': 26.8, 'util': 84.5, 'ctb': 15.7, 'dtc': 6.8},
        }
        
        for ticker in tickers:
            if ticker in squeeze_profiles:
                profile = squeeze_profiles[ticker]
            else:
                # Generate category-appropriate data
                random.seed(hash(ticker) % 10000)
                
                if ticker in self.ticker_universe.get('top_meme_stocks', []):
                    si_base = random.uniform(15, 35)
                    util_base = random.uniform(75, 95)
                    ctb_base = random.uniform(10, 40)
                elif ticker in self.ticker_universe.get('biotech_squeeze', []):
                    si_base = random.uniform(20, 40)
                    util_base = random.uniform(80, 98)
                    ctb_base = random.uniform(15, 60)
                elif ticker in self.ticker_universe.get('large_cap_samples', []):
                    si_base = random.uniform(1, 6)
                    util_base = random.uniform(20, 50)
                    ctb_base = random.uniform(0.5, 3)
                else:
                    si_base = random.uniform(8, 25)
                    util_base = random.uniform(50, 85)
                    ctb_base = random.uniform(3, 20)
                
                profile = {
                    'si': round(si_base, 1),
                    'util': round(util_base, 1),
                    'ctb': round(ctb_base, 1),
                    'dtc': round(si_base * random.uniform(0.2, 0.5), 1)
                }
            
            mock_data[ticker] = {
                'short_interest': profile['si'],
                'utilization': profile['util'],
                'cost_to_borrow': profile['ctb'],
                'days_to_cover': profile['dtc'],
                'data_quality': 'smart_mock',
                'source_endpoints': ['enhanced_mock']
            }
        
        return mock_data
    
    def calculate_squeeze_score_optimized(self, ortex_data, price_data):
        """Optimized squeeze scoring for speed"""
        try:
            si = ortex_data.get('short_interest', 0)
            util = ortex_data.get('utilization', 0)
            ctb = ortex_data.get('cost_to_borrow', 0)
            dtc = ortex_data.get('days_to_cover', 0)
            price_change_pct = price_data.get('price_change_pct', 0)
            
            # Fast scoring calculation
            si_score = min(si * 1.2, 35)
            util_score = min(util * 0.25, 25)
            ctb_score = min(ctb * 0.8, 20)
            dtc_score = min(dtc * 1.5, 15)
            momentum_score = max(price_change_pct * 0.3, 0) if price_change_pct > 0 else 0
            
            total_score = int(si_score + util_score + ctb_score + dtc_score + momentum_score)
            
            # Fast risk assessment
            risk_factors = []
            if si > 25: risk_factors.append("EXTREME_SHORT_INTEREST")
            if util > 90: risk_factors.append("HIGH_UTILIZATION")
            if ctb > 20: risk_factors.append("HIGH_BORROWING_COSTS")
            
            # Quick categorization
            if total_score >= 80:
                squeeze_type = "Extreme Squeeze Risk"
            elif total_score >= 65:
                squeeze_type = "High Squeeze Risk"
            elif total_score >= 45:
                squeeze_type = "Moderate Squeeze Risk"
            else:
                squeeze_type = "Low Risk"
            
            return {
                'squeeze_score': total_score,
                'squeeze_type': squeeze_type,
                'risk_factors': risk_factors,
                'score_breakdown': {
                    'short_interest': int(si_score),
                    'utilization': int(util_score),
                    'cost_to_borrow': int(ctb_score),
                    'days_to_cover': int(dtc_score),
                    'momentum': int(momentum_score)
                }
            }
        except Exception:
            return {'squeeze_score': 0, 'squeeze_type': 'Error', 'risk_factors': []}
    
    def perform_optimized_scan(self, ortex_key=None, filters=None):
        """Optimized scan with timeout prevention"""
        start_time = time.time()
        print(f"🚀 Starting optimized squeeze scan...")
        
        # Apply filters and optimize scan size
        scan_tickers = self.master_ticker_list.copy()
        
        if filters:
            if filters.get('categories'):
                filtered_tickers = []
                for category in filters['categories']:
                    if category in self.ticker_universe:
                        filtered_tickers.extend(self.ticker_universe[category])
                scan_tickers = list(set(filtered_tickers))
            
            requested_size = filters.get('max_tickers', 20)
            scan_optimization = self.calculate_optimal_scan_size(requested_size)
            scan_tickers = scan_tickers[:scan_optimization['optimal_size']]
        else:
            scan_tickers = scan_tickers[:15]  # Default safe size
        
        print(f"📊 Scanning {len(scan_tickers)} tickers (optimized for performance)")
        
        # Fast price data retrieval
        print(f"💰 Fetching live price data...")
        price_data = self.get_yahoo_price_data_fast(scan_tickers, max_workers=12)
        successful_tickers = [t for t in scan_tickers if t in price_data]
        
        print(f"✅ Got price data for {len(successful_tickers)} tickers")
        
        # Fast Ortex data attempt (limited to prevent timeout)
        ortex_data = {}
        if ortex_key and len(successful_tickers) <= 10:  # Only try Ortex for small batches
            print(f"🔍 Attempting live Ortex data for top candidates...")
            for ticker in successful_tickers[:5]:  # Limit to top 5 for speed
                ortex_result = self.get_fast_ortex_data(ticker, ortex_key)
                if ortex_result:
                    ortex_data[ticker] = ortex_result
                    print(f"  ✅ Live Ortex data for {ticker}")
        
        # Fill remaining with smart mock data (preserve live data)
        mock_data = self.generate_smart_mock_data(successful_tickers)
        for ticker in successful_tickers:
            if ticker not in ortex_data:
                ortex_data[ticker] = mock_data[ticker]
            else:
                # Ensure live data is properly marked
                ortex_data[ticker]['data_quality'] = 'live_ortex'
                print(f"  🟢 Confirmed live data for {ticker}")
        
        # Fast analysis
        print(f"🎯 Calculating squeeze scores...")
        results = []
        
        for ticker in successful_tickers:
            if ticker in ortex_data:
                squeeze_metrics = self.calculate_squeeze_score_optimized(
                    ortex_data[ticker], price_data[ticker]
                )
                
                result = {
                    'ticker': ticker,
                    'squeeze_score': squeeze_metrics['squeeze_score'],
                    'squeeze_type': squeeze_metrics['squeeze_type'],
                    'current_price': price_data[ticker]['current_price'],
                    'price_change': price_data[ticker]['price_change'],
                    'price_change_pct': price_data[ticker]['price_change_pct'],
                    'volume': price_data[ticker]['volume'],
                    'ortex_data': ortex_data[ticker],
                    'risk_factors': squeeze_metrics.get('risk_factors', []),
                    'data_quality': ortex_data[ticker].get('data_quality', 'mock'),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)
        
        # Sort by squeeze score
        results.sort(key=lambda x: x['squeeze_score'], reverse=True)
        
        total_time = time.time() - start_time
        print(f"✅ Optimized scan complete! {len(results)} tickers in {total_time:.1f}s")
        
        # Update performance stats
        if len(results) > 0:
            self.performance_stats['avg_ticker_time'] = total_time / len(results)
        
        return {
            'results': results,
            'scan_stats': {
                'total_tickers_scanned': len(scan_tickers),
                'successful_analysis': len(results),
                'live_ortex_count': len([r for r in results if r['data_quality'] == 'live_ortex']),
                'scan_time_seconds': round(total_time, 1),
                'performance_rating': 'excellent' if total_time < 15 else 'good' if total_time < 30 else 'acceptable',
                'top_score': results[0]['squeeze_score'] if results else 0,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def do_GET(self):
        if self.path == '/':
            self.send_optimized_scanner_html()
        elif self.path == '/api/health':
            self.send_health()
        elif self.path == '/api/performance-stats':
            self.send_performance_stats()
        else:
            self.send_404()
    
    def do_POST(self):
        if self.path == '/api/optimized-scan':
            self.handle_optimized_scan()
        else:
            self.send_404()
    
    def handle_optimized_scan(self):
        """Handle optimized scan requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode()) if post_data else {}
            
            ortex_key = data.get('ortex_key', '')
            filters = data.get('filters', {})
            
            # Calculate optimization recommendations
            requested_size = filters.get('max_tickers', 20)
            optimization = self.calculate_optimal_scan_size(requested_size)
            
            # Perform optimized scan
            scan_results = self.perform_optimized_scan(ortex_key, filters)
            
            response = {
                'success': True,
                'scan_results': scan_results['results'],
                'scan_stats': scan_results['scan_stats'],
                'optimization_info': optimization,
                'message': f"Optimized scan completed - {len(scan_results['results'])} tickers analyzed in {scan_results['scan_stats']['scan_time_seconds']}s"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {'success': False, 'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def send_performance_stats(self):
        """Send performance statistics"""
        stats = {
            'performance_metrics': self.performance_stats,
            'ticker_universe': {name: len(tickers) for name, tickers in self.ticker_universe.items()},
            'total_tickers': len(self.master_ticker_list),
            'optimization_recommendations': {
                'safe_batch_sizes': {
                    'small': '5-10 tickers (fast, reliable)',
                    'medium': '10-20 tickers (balanced)',
                    'large': '20+ tickers (use high min score)'
                },
                'timeout_prevention': {
                    'recommended_max': self.performance_stats['max_safe_batch_size'],
                    'estimated_time_per_ticker': self.performance_stats['avg_ticker_time']
                }
            }
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode())
    
    def send_optimized_scanner_html(self):
        """Send optimized scanner interface"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>⚡ Ultimate Squeeze Scanner - Optimized Performance</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
                    color: #e0e0e0;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .header h1 {
                    color: #ff6b6b;
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                    text-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
                }
                .performance-banner {
                    background: linear-gradient(45deg, #1a4c96, #2196F3);
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    text-align: center;
                    border: 1px solid #2196F3;
                }
                .controls-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 20px;
                    background: #1a1a2e;
                    padding: 25px;
                    border-radius: 15px;
                    margin-bottom: 25px;
                    border: 1px solid #3a3a4e;
                }
                .control-group {
                    margin-bottom: 15px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    color: #a0a0b0;
                    font-weight: bold;
                    font-size: 0.9rem;
                }
                input, select {
                    width: 100%;
                    padding: 10px;
                    background: #2a2a3e;
                    border: 1px solid #4a4a5e;
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 14px;
                    box-sizing: border-box;
                }
                .btn-optimized {
                    background: linear-gradient(45deg, #2196F3, #64B5F6);
                    color: white;
                    border: none;
                    padding: 15px 25px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    width: 100%;
                    margin-top: 10px;
                }
                .btn-optimized:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
                }
                .optimization-info {
                    background: #1a2e1a;
                    border: 1px solid #4CAF50;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                    font-size: 0.9rem;
                }
                .results-optimized {
                    display: grid;
                    gap: 12px;
                }
                .result-card-compact {
                    background: #1a1a2e;
                    border-radius: 8px;
                    padding: 15px;
                    border-left: 4px solid #4CAF50;
                    display: grid;
                    grid-template-columns: 80px 1fr 120px 100px 80px;
                    gap: 15px;
                    align-items: center;
                }
                .ticker-compact {
                    text-align: center;
                }
                .ticker-symbol-compact {
                    font-size: 1.2rem;
                    font-weight: bold;
                    color: #ff6b6b;
                }
                .ticker-price-compact {
                    color: #a0a0b0;
                    font-size: 0.8rem;
                }
                .metrics-compact {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 8px;
                }
                .metric-compact {
                    background: #2a2a3e;
                    padding: 6px;
                    border-radius: 4px;
                    text-align: center;
                }
                .metric-value-compact {
                    font-weight: bold;
                    color: #4CAF50;
                    font-size: 0.9rem;
                }
                .metric-label-compact {
                    font-size: 0.7rem;
                    color: #a0a0b0;
                }
                .score-display {
                    text-align: center;
                }
                .score-number-compact {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #ff6b6b;
                }
                .score-type-compact {
                    font-size: 0.7rem;
                    padding: 3px 6px;
                    border-radius: 10px;
                    font-weight: bold;
                }
                .data-quality-compact {
                    text-align: center;
                    font-size: 0.8rem;
                }
                .live-indicator {
                    color: #4CAF50;
                    font-weight: bold;
                }
                .mock-indicator {
                    color: #ff9800;
                }
                .performance-stats {
                    background: #1a1a2e;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 10px;
                }
                .stat-compact {
                    text-align: center;
                    background: #2a2a3e;
                    padding: 10px;
                    border-radius: 6px;
                }
                .stat-value-compact {
                    font-size: 1.3rem;
                    font-weight: bold;
                    color: #2196F3;
                }
                .stat-label-compact {
                    font-size: 0.8rem;
                    color: #a0a0b0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ Ultimate Squeeze Scanner</h1>
                    <p>Optimized Performance - Fast Multi-Ticker Analysis</p>
                </div>
                
                <div class="performance-banner">
                    <strong>⚡ Performance Optimized</strong> - Timeout prevention, smart batch sizing, and fast processing
                </div>
                
                <div class="controls-grid">
                    <div>
                        <div class="control-group">
                            <label for="ortexKey">Ortex API Key</label>
                            <input type="text" id="ortexKey" value="zKBk0B8x.WWmEKkC5885KMymycx6s6kOeVmG5UHnG">
                        </div>
                        
                        <div class="control-group">
                            <label for="categories">Categories</label>
                            <select id="categories" multiple>
                                <option value="top_meme_stocks" selected>Top Meme Stocks</option>
                                <option value="high_short_interest">High Short Interest</option>
                                <option value="biotech_squeeze">Biotech Squeeze</option>
                                <option value="small_cap_movers">Small Cap Movers</option>
                                <option value="large_cap_samples">Large Cap Samples</option>
                            </select>
                        </div>
                    </div>
                    
                    <div>
                        <div class="control-group">
                            <label for="maxTickers">Max Tickers</label>
                            <input type="number" id="maxTickers" value="15" min="5" max="30">
                            <small style="color: #a0a0b0;">Recommended: 5-15 for fast results</small>
                        </div>
                        
                        <div class="control-group">
                            <label for="minScore">Min Squeeze Score</label>
                            <input type="number" id="minScore" value="40" min="0" max="100">
                            <small style="color: #a0a0b0;">Higher scores = fewer results, faster scanning</small>
                        </div>
                    </div>
                    
                    <div>
                        <div class="optimization-info">
                            <strong>🎯 Smart Optimization:</strong><br>
                            • Automatic batch sizing<br>
                            • Timeout prevention<br>  
                            • Fast data processing<br>
                            • Live data when available
                        </div>
                        
                        <button class="btn-optimized" onclick="startOptimizedScan()">
                            ⚡ Start Optimized Scan
                        </button>
                    </div>
                </div>
                
                <div id="scanResults" style="display: none;">
                    <!-- Results will populate here -->
                </div>
            </div>
            
            <script>
                async function startOptimizedScan() {
                    const ortexKey = document.getElementById('ortexKey').value.trim();
                    const categoriesSelect = document.getElementById('categories');
                    const selectedCategories = Array.from(categoriesSelect.selectedOptions).map(option => option.value);
                    const maxTickers = parseInt(document.getElementById('maxTickers').value);
                    const minScore = parseInt(document.getElementById('minScore').value);
                    
                    const scanBtn = document.querySelector('.btn-optimized');
                    const resultsDiv = document.getElementById('scanResults');
                    
                    // Show loading
                    scanBtn.disabled = true;
                    scanBtn.textContent = '⚡ Optimizing & Scanning...';
                    resultsDiv.style.display = 'block';
                    resultsDiv.innerHTML = `
                        <div style="text-align: center; padding: 30px; color: #2196F3; font-size: 1.1rem;">
                            ⚡ Optimized scan in progress...<br>
                            <small>Smart batch processing for ${maxTickers} tickers</small>
                        </div>
                    `;
                    
                    try {
                        const response = await fetch('/api/optimized-scan', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                ortex_key: ortexKey,
                                filters: {
                                    categories: selectedCategories,
                                    max_tickers: maxTickers,
                                    min_score: minScore
                                }
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            displayOptimizedResults(data.scan_results, data.scan_stats, data.optimization_info, minScore);
                        } else {
                            resultsDiv.innerHTML = `<div style="color: #f44336; padding: 20px; text-align: center;">❌ Error: ${data.error}</div>`;
                        }
                        
                    } catch (error) {
                        resultsDiv.innerHTML = `<div style="color: #f44336; padding: 20px; text-align: center;">❌ Network error: ${error.message}</div>`;
                    }
                    
                    // Reset button
                    scanBtn.disabled = false;
                    scanBtn.textContent = '⚡ Start Optimized Scan';
                }
                
                function displayOptimizedResults(results, stats, optimization, minScore) {
                    const resultsDiv = document.getElementById('scanResults');
                    const filteredResults = results.filter(r => r.squeeze_score >= minScore);
                    
                    let html = `
                        <div class="performance-stats">
                            <div class="stat-compact">
                                <div class="stat-value-compact">${stats.successful_analysis}</div>
                                <div class="stat-label-compact">Analyzed</div>
                            </div>
                            <div class="stat-compact">
                                <div class="stat-value-compact">${filteredResults.length}</div>
                                <div class="stat-label-compact">Above Min</div>
                            </div>
                            <div class="stat-compact">
                                <div class="stat-value-compact">${stats.live_ortex_count}</div>
                                <div class="stat-label-compact">Live Data</div>
                            </div>
                            <div class="stat-compact">
                                <div class="stat-value-compact">${stats.scan_time_seconds}s</div>
                                <div class="stat-label-compact">Scan Time</div>
                            </div>
                            <div class="stat-compact">
                                <div class="stat-value-compact">${stats.performance_rating}</div>
                                <div class="stat-label-compact">Performance</div>
                            </div>
                        </div>
                        
                        <div class="results-optimized">
                    `;
                    
                    filteredResults.forEach(result => {
                        const isLive = result.data_quality === 'live_ortex';
                        html += `
                            <div class="result-card-compact" style="border-left-color: ${getSqueezeColor(result.squeeze_score)}">
                                <div class="ticker-compact">
                                    <div class="ticker-symbol-compact">${result.ticker}</div>
                                    <div class="ticker-price-compact">$${result.current_price}</div>
                                    <div class="ticker-price-compact" style="color: ${result.price_change >= 0 ? '#4CAF50' : '#f44336'}">
                                        ${result.price_change >= 0 ? '+' : ''}${result.price_change_pct}%
                                    </div>
                                </div>
                                
                                <div class="metrics-compact">
                                    <div class="metric-compact">
                                        <div class="metric-value-compact">${result.ortex_data.short_interest}%</div>
                                        <div class="metric-label-compact">Short Int</div>
                                    </div>
                                    <div class="metric-compact">
                                        <div class="metric-value-compact">${result.ortex_data.utilization}%</div>
                                        <div class="metric-label-compact">Utilization</div>
                                    </div>
                                    <div class="metric-compact">
                                        <div class="metric-value-compact">${result.ortex_data.cost_to_borrow}%</div>
                                        <div class="metric-label-compact">CTB</div>
                                    </div>
                                    <div class="metric-compact">
                                        <div class="metric-value-compact">${result.ortex_data.days_to_cover}</div>
                                        <div class="metric-label-compact">DTC</div>
                                    </div>
                                </div>
                                
                                <div class="score-display">
                                    <div class="score-number-compact">${result.squeeze_score}</div>
                                    <div class="score-type-compact" style="background: ${getSqueezeColor(result.squeeze_score)}">
                                        ${result.squeeze_type.replace(' Risk', '')}
                                    </div>
                                </div>
                                
                                <div style="display: flex; flex-direction: column; gap: 3px;">
                                    ${result.risk_factors.slice(0, 2).map(factor => 
                                        `<div style="background: #f44336; color: white; padding: 2px 6px; border-radius: 8px; font-size: 0.6rem; text-align: center;">${factor.replace('_', ' ')}</div>`
                                    ).join('')}
                                </div>
                                
                                <div class="data-quality-compact">
                                    <div class="${isLive ? 'live-indicator' : 'mock-indicator'}">
                                        ${isLive ? '🟢 LIVE' : '🟡 EST'}
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    resultsDiv.innerHTML = html;
                }
                
                function getSqueezeColor(score) {
                    if (score >= 80) return '#d32f2f';
                    if (score >= 65) return '#f44336';
                    if (score >= 45) return '#ff9800';
                    if (score >= 25) return '#2196F3';
                    return '#4CAF50';
                }
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def send_health(self):
        """Send API health check"""
        health_data = {
            'status': 'healthy',
            'message': 'Ultimate Squeeze Scanner API v9.0 - Performance Optimized',
            'timestamp': datetime.now().isoformat(),
            'version': '9.0.0-performance-optimized',
            'features': {
                'optimized_scanning': 'active',
                'timeout_prevention': 'active',
                'smart_batch_sizing': 'active',
                'fast_ortex_discovery': 'active',
                'performance_monitoring': 'active'
            },
            'performance_stats': self.performance_stats,
            'ticker_universe_size': len(self.master_ticker_list)
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(health_data).encode())
    
    def send_404(self):
        """Send 404 error"""
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'error': 'Not Found'}
        self.wfile.write(json.dumps(response).encode())
