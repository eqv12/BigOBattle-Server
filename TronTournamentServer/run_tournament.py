# Save this as run_tournament.py in your root project folder

from server.logic import matchmaker
from server.logic import tournament_manager

def main():
    print("🚀 Initializing Tournament Server...")
    
    # 1. Start the matchmaker system with its background workers
    # This returns the queue that we'll use to submit matches
    match_queue = matchmaker.start_matchmaker()
    
    # 2. Run the tournament. The manager will feed matches into the queue.
    tournament_manager.run_swiss_tournament(match_queue)
    
    print("\n✅ Tournament has concluded. Shutting down.")

if __name__ == "__main__":
    main()