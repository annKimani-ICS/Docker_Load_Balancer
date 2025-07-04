  
        Hash function for virtual servers: Φ(i,j) = i² + j + 2j + 25
        This function determines where to place virtual server j of server i
        
        Arguments used:
            i: Server ID (integer)
            j: Virtual server number (1-9)
            

        
        Mathematical breakdown:
        - i² : Spreads servers based on their ID squared
        - j : Adds the virtual server number
        - 2j : Adds twice the virtual server number for more spread
        - 25 : Constant offset to avoid clustering at slot 0
        - % total_slots : Ensures result is within valid slot range
  
