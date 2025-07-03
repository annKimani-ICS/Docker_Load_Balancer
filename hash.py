import math

class ConsistentHash:
    def __init__(self, num_servers=3, total_slots=512):
        self.total_slots = total_slots
        self.virtual_servers = {}  # {slot: server_name}
        
        # Add initial servers with virtual copies
        for server_id in range(1, num_servers + 1):
            self._add_server(f"Server_{server_id}")
    
    def _add_server(self, server_name):
        """Add a server with its virtual copies"""
        server_id = int(server_name.split('_')[1])
        
        # Create 9 virtual copies (K=9)
        for j in range(1, 10):
            slot = self._hash_virtual(server_id, j)
            
            # Handle slot collisions
            while slot in self.virtual_servers:
                slot = (slot + j*j) % self.total_slots  # Quadratic probing
            
            self.virtual_servers[slot] = server_name
    
    def _hash_virtual(self, i, j):
        """Hash function for virtual servers: Φ(i,j) = i² + j + 2j + 25"""
        return (i*i + j + 2*j + 25) % self.total_slots
    
    def _hash_request(self, request_id):
        """Hash function for requests: H(i) = i² + 2i + 17"""
        return (request_id*request_id + 2*request_id + 17) % self.total_slots
    
    def get_server(self, request_id):
        """Find which server should handle this request"""
        if not self.virtual_servers:
            return None
            
        slot = self._hash_request(request_id)
        
        # Find next available server (clockwise)
        while slot not in self.virtual_servers:
            slot = (slot + 1) % self.total_slots
        
        return self.virtual_servers[slot]
    
    # Alias for compatibility with load balancer
    def get_server_for_request(self, request_id):
        return self.get_server(request_id)