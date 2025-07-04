import math

class ConsistentHash:
    def __init__(self, num_servers=3, total_slots=512):

        self.total_slots = total_slots
        self.virtual_servers = {}  # Dictionary mapping {slot: server_name}
        
        # Add initial servers with virtual copies
        # This creates Server_1, Server_2, Server_3, etc.
        for server_id in range(1, num_servers + 1):
            self._add_server(f"Server_{server_id}")
    
    def _add_server(self, server_name):
        """
        Add a server with its virtual copies to the hash ring
        
        Each server gets K=9 virtual copies placed at different slots
        to ensure better load distribution
        
        Args:
            server_name: Name of the server to add (e.g., "Server_1")
        """
        
        try:
            server_id = int(server_name.split('_')[1])
        except (IndexError, ValueError):
            print(f"Warning: Invalid server name format: {server_name}")
            return False
        
        # Create K=9 virtual copies of this server
        for j in range(1, 10):  # j goes from 1 to 9
            # Calculate slot using virtual server hash function
            slot = self._hash_virtual(server_id, j)
            
            # Handle slot collisions using quadratic probing
            # If slot is already occupied, try slot + j², then slot + 2j², etc.
            original_slot = slot
            probe_count = 0
            while slot in self.virtual_servers and probe_count < self.total_slots:
                slot = (original_slot + j * j * (probe_count + 1)) % self.total_slots
                probe_count += 1
            
            # If we couldn't find an empty slot, skip this virtual server
            if slot in self.virtual_servers:
                print(f"Warning: Could not place virtual server {server_name}_{j}")
                continue
            
            # Place the virtual server in the slot
            self.virtual_servers[slot] = server_name
        
        print(f"Added server {server_name} with {len([s for s in self.virtual_servers.values() if s == server_name])} virtual copies")
        return True
    
    def _hash_virtual(self, i, j):

        return (i * i + j + 2 * j + 25) % self.total_slots
    
    def _hash_request(self, request_id):

        return (request_id * request_id + 2 * request_id + 17) % self.total_slots
    
    def get_server(self, request_id):

        if not self.virtual_servers:
            return None
        
        # Get the slot for this request
        slot = self._hash_request(request_id)
        
        # Find next available server (clockwise search)
        # This ensures consistent mapping even when servers are added/removed
        original_slot = slot
        while slot not in self.virtual_servers:
            slot = (slot + 1) % self.total_slots
            # Prevent infinite loop if no servers exist
            if slot == original_slot:
                return None
        
        return self.virtual_servers[slot]
    
    def remove_server(self, server_name):

        if not server_name:
            return False
        
        # Find and collect all virtual copies of this server
        slots_to_remove = []
        for slot, server in self.virtual_servers.items():
            if server == server_name:
                slots_to_remove.append(slot)
        
        # Remove all the slots
        for slot in slots_to_remove:
            del self.virtual_servers[slot]
        
        removed_count = len(slots_to_remove)
        if removed_count > 0:
            print(f"Removed {removed_count} virtual copies of {server_name}")
            return True
        else:
            print(f"Server {server_name} not found in hash ring")
            return False
    
    # Alias for compatibility with load balancer
    def get_server_for_request(self, request_id):
        """Alias for get_server method for backward compatibility"""
        return self.get_server(request_id)
    
    def get_server_distribution(self):
        """
        Get statistics about server distribution in the hash ring
        
        Returns:
            Dictionary with server names as keys and virtual copy counts as values
        """
        distribution = {}
        for server in self.virtual_servers.values():
            distribution[server] = distribution.get(server, 0) + 1
        return distribution
    
