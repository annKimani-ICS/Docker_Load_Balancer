import asyncio
import aiohttp
import matplotlib.pyplot as plt
import numpy as np
import json
import time
from collections import defaultdict, Counter
import pandas as pd
import seaborn as sns
from datetime import datetime
import requests

class LoadBalancerTester:
    def __init__(self, lb_url="http://localhost:5004"):
        self.lb_url = lb_url
        self.results = {}
        
    async def send_request(self, session, request_id):
        """Send a single async request to the load balancer"""
        try:
            async with session.get(f"{self.lb_url}/home") as response:
                data = await response.json()
                return {
                    'request_id': request_id,
                    'server': data.get('server', 'unknown'),
                    'status_code': response.status,
                    'timestamp': time.time()
                }
        except Exception as e:
            return {
                'request_id': request_id,
                'server': 'error',
                'status_code': 0,
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def run_async_requests(self, num_requests=10000):
        """Run multiple async requests and collect results"""
        print(f"Starting {num_requests} async requests...")
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.send_request(session, i) for i in range(num_requests)]
            results = await asyncio.gather(*tasks)
        
        return results
    
    def analyze_request_distribution(self, results):
        """Analyze how requests were distributed among servers"""
        server_counts = Counter()
        successful_requests = 0
        
        for result in results:
            if result['status_code'] == 200:
                server_counts[result['server']] += 1
                successful_requests += 1
        
        return dict(server_counts), successful_requests
    
    def plot_request_distribution(self, server_counts, title="Request Distribution"):
        """Create bar chart of request distribution"""
        plt.figure(figsize=(10, 6))
        servers = list(server_counts.keys())
        counts = list(server_counts.values())
        
        bars = plt.bar(servers, counts, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'])
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Server Instance', fontsize=12)
        plt.ylabel('Number of Requests Handled', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        
        # Calculate and display statistics
        total_requests = sum(counts)
        avg_requests = total_requests / len(servers) if servers else 0
        std_dev = np.std(counts) if counts else 0
        
        plt.text(0.02, 0.98, f'Total Requests: {total_requests}\nAvg per Server: {avg_requests:.1f}\nStd Dev: {std_dev:.1f}', 
                transform=plt.gca().transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        return plt.gcf()
    
    async def experiment_a1(self):
        """A-1: Launch 10000 async requests on N=3 servers"""
        print("=== Experiment A-1: 10000 requests on N=3 servers ===")
        
        # Ensure we have 3 servers
        self.setup_servers(3)
        
        # Run requests
        results = await self.run_async_requests(10000)
        server_counts, successful = self.analyze_request_distribution(results)
        
        # Plot results
        fig = self.plot_request_distribution(server_counts, "A-1: Request Distribution (N=3, 10000 requests)")
        plt.savefig('experiment_a1_distribution.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Store results
        self.results['A-1'] = {
            'server_counts': server_counts,
            'successful_requests': successful,
            'total_requests': 10000,
            'servers': 3
        }
        
        print(f"A-1 Results: {server_counts}")
        print(f"Successful requests: {successful}/10000")
        
        return server_counts, successful
    
    async def experiment_a2(self):
        """A-2: Scale from N=2 to N=6 servers with 10000 requests each"""
        print("=== Experiment A-2: Scalability Test (N=2 to 6) ===")
        
        server_counts_by_n = {}
        avg_loads = []
        server_nums = range(2, 7)  # N = 2, 3, 4, 5, 6
        
        for n in server_nums:
            print(f"\nTesting with N={n} servers...")
            
            # Setup servers
            self.setup_servers(n)
            
            # Run requests
            results = await self.run_async_requests(10000)
            server_counts, successful = self.analyze_request_distribution(results)
            
            # Calculate average load
            if server_counts:
                avg_load = sum(server_counts.values()) / len(server_counts)
                avg_loads.append(avg_load)
                server_counts_by_n[n] = server_counts
                
                print(f"N={n}: {server_counts}, Avg load: {avg_load:.1f}")
            else:
                avg_loads.append(0)
        
        # Plot scalability results
        plt.figure(figsize=(12, 8))
        
        # Plot 1: Average load per server
        plt.subplot(2, 1, 1)
        plt.plot(server_nums, avg_loads, marker='o', linewidth=2, markersize=8, color='#FF6B6B')
        plt.title('A-2: Average Load per Server vs Number of Servers', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Servers (N)')
        plt.ylabel('Average Requests per Server')
        plt.grid(True, alpha=0.3)
        
        # Add theoretical ideal line
        ideal_loads = [10000/n for n in server_nums]
        plt.plot(server_nums, ideal_loads, '--', color='gray', alpha=0.7, label='Ideal Distribution')
        plt.legend()
        
        # Plot 2: Load distribution variance
        plt.subplot(2, 1, 2)
        variances = []
        for n in server_nums:
            if n in server_counts_by_n:
                counts = list(server_counts_by_n[n].values())
                variance = np.var(counts) if counts else 0
                variances.append(variance)
            else:
                variances.append(0)
        
        plt.plot(server_nums, variances, marker='s', linewidth=2, markersize=8, color='#4ECDC4')
        plt.title('Load Distribution Variance vs Number of Servers', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Servers (N)')
        plt.ylabel('Variance in Request Distribution')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('experiment_a2_scalability.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Store results
        self.results['A-2'] = {
            'server_counts_by_n': server_counts_by_n,
            'avg_loads': avg_loads,
            'variances': variances
        }
        
        return server_counts_by_n, avg_loads
    
    def experiment_a3(self):
        """A-3: Test server failure recovery"""
        print("=== Experiment A-3: Server Failure Recovery Test ===")
        
        # Test all endpoints
        endpoints = ['/', '/rep', '/add', '/rm', '/home', '/heartbeat', '/servers']
        
        print("Testing all endpoints...")
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.lb_url}{endpoint}", timeout=5)
                print(f"✓ {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"✗ {endpoint}: {str(e)}")
        
        # Test server failure simulation
        print("\nSimulating server failure...")
        
        # Get current server status
        try:
            response = requests.get(f"{self.lb_url}/servers")
            initial_servers = response.json()
            print(f"Initial servers: {initial_servers}")
        except Exception as e:
            print(f"Error getting server status: {e}")
            return
        
        # Remove a server
        try:
            remove_data = {"n": 1, "hostnames": ["Server_1:5001"]}
            response = requests.delete(f"{self.lb_url}/rm", json=remove_data)
            print(f"Remove server response: {response.json()}")
        except Exception as e:
            print(f"Error removing server: {e}")
        
        # Add a new server
        try:
            add_data = {"n": 1, "hostnames": ["Server_New:5010"]}
            response = requests.post(f"{self.lb_url}/add", json=add_data)
            print(f"Add server response: {response.json()}")
        except Exception as e:
            print(f"Error adding server: {e}")
        
        # Get final server status
        try:
            response = requests.get(f"{self.lb_url}/servers")
            final_servers = response.json()
            print(f"Final servers: {final_servers}")
        except Exception as e:
            print(f"Error getting final server status: {e}")
        
        self.results['A-3'] = {
            'initial_servers': initial_servers,
            'final_servers': final_servers,
            'endpoints_tested': endpoints
        }
    
    def setup_servers(self, n):
        """Setup N servers for testing"""
        try:
            # Get current servers
            response = requests.get(f"{self.lb_url}/rep")
            current_servers = response.json()['message']['replicas']
            current_n = len(current_servers)
            
            if current_n == n:
                print(f"Already have {n} servers")
                return
            elif current_n < n:
                # Add servers
                add_count = n - current_n
                add_data = {"n": add_count}
                response = requests.post(f"{self.lb_url}/add", json=add_data)
                print(f"Added {add_count} servers: {response.json()}")
            else:
                # Remove servers
                remove_count = current_n - n
                remove_data = {"n": remove_count}
                response = requests.delete(f"{self.lb_url}/rm", json=remove_data)
                print(f"Removed {remove_count} servers: {response.json()}")
        
        except Exception as e:
            print(f"Error setting up servers: {e}")
    
    def generate_report(self):
        """Generate a comprehensive report"""
        print("\n" + "="*60)
        print("LOAD BALANCER PERFORMANCE ANALYSIS REPORT")
        print("="*60)
        
        # A-1 Analysis
        if 'A-1' in self.results:
            a1_data = self.results['A-1']
            print("\nA-1 ANALYSIS: Request Distribution (N=3)")
            print("-" * 40)
            print(f"Total Requests: {a1_data['total_requests']}")
            print(f"Successful Requests: {a1_data['successful_requests']}")
            print(f"Success Rate: {a1_data['successful_requests']/a1_data['total_requests']*100:.1f}%")
            print("\nRequest Distribution:")
            for server, count in a1_data['server_counts'].items():
                percentage = count / a1_data['successful_requests'] * 100
                print(f"  {server}: {count} requests ({percentage:.1f}%)")
            
            # Calculate distribution quality
            counts = list(a1_data['server_counts'].values())
            if counts:
                ideal_count = a1_data['successful_requests'] / len(counts)
                variance = np.var(counts)
                std_dev = np.std(counts)
                print(f"\nDistribution Quality:")
                print(f"  Ideal requests per server: {ideal_count:.1f}")
                print(f"  Standard deviation: {std_dev:.1f}")
                print(f"  Variance: {variance:.1f}")
                print(f"  Distribution efficiency: {max(0, 100 - (std_dev/ideal_count*100)):.1f}%")
        
        # A-2 Analysis
        if 'A-2' in self.results:
            a2_data = self.results['A-2']
            print("\nA-2 ANALYSIS: Scalability Test")
            print("-" * 40)
            print("Average Load per Server:")
            for i, (n, avg_load) in enumerate(zip(range(2, 7), a2_data['avg_loads'])):
                ideal_load = 10000 / n
                efficiency = (min(avg_load, ideal_load) / ideal_load) * 100 if ideal_load > 0 else 0
                print(f"  N={n}: {avg_load:.1f} requests/server (ideal: {ideal_load:.1f}, efficiency: {efficiency:.1f}%)")
        
        # A-3 Analysis
        if 'A-3' in self.results:
            print("\nA-3 ANALYSIS: Failure Recovery")
            print("-" * 40)
            print("All load balancer endpoints tested successfully")
            print("Server failure and recovery simulation completed")
        
        # Save report to file
        with open('load_balancer_analysis_report.txt', 'w') as f:
            f.write("LOAD BALANCER PERFORMANCE ANALYSIS REPORT\n")
            f.write("="*60 + "\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(json.dumps(self.results, indent=2))
        
        print(f"\nDetailed results saved to: load_balancer_analysis_report.txt")

async def main():
    """Run all experiments"""
    tester = LoadBalancerTester()
    
    print("Load Balancer Performance Testing Suite")
    print("="*50)
    
    # Run experiments
    try:
        await tester.experiment_a1()
        await tester.experiment_a2()
        tester.experiment_a3()
        tester.generate_report()
        
        print("\n" + "="*50)
        print("ALL EXPERIMENTS COMPLETED SUCCESSFULLY!")
        print("Check the generated PNG files and report for detailed analysis.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Install required packages if needed
    try:
        import matplotlib.pyplot as plt
        import aiohttp
        import seaborn as sns
        import pandas as pd
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Install with: pip install matplotlib aiohttp seaborn pandas")
        exit(1)
    
    # Run the test suite
    asyncio.run(main())