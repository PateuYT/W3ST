import json
import os
from datetime import datetime
from typing import Optional, Dict, List

class TicketDatabase:
    def __init__(self):
        self.files = {
            'tickets': 'data/tickets.json',
            'stats': 'data/stats.json',
            'blacklist': 'data/blacklist.json',
            'ratings': 'data/ratings.json'
        }
        self._ensure_data_dir()
        self.data = {key: self._load_file(path) for key, path in self.files.items()}
        self.ticket_counter = self._get_last_ticket_number()
    
    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)
        for path in self.files.values():
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump({} if 'blacklist' not in path else [], f)
    
    def _load_file(self, path: str):
        with open(path, 'r') as f:
            return json.load(f)
    
    def _save_file(self, key: str):
        with open(self.files[key], 'w') as f:
            json.dump(self.data[key], f, indent=2, default=str)
    
    def _get_last_ticket_number(self) -> int:
        tickets = self.data['tickets']
        if not tickets:
            return 0
        numbers = [int(tid.split('-')[1]) for tid in tickets.keys() if tid.startswith('ticket-')]
        return max(numbers) if numbers else 0
    
    # Tickets
    def create_ticket(self, user_id: str, channel_id: str, ticket_type: str) -> str:
        self.ticket_counter += 1
        ticket_id = f"ticket-{self.ticket_counter:04d}"
        
        self.data['tickets'][ticket_id] = {
            "id": ticket_id,
            "user_id": user_id,
            "channel_id": channel_id,
            "type": ticket_type,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "claimed_by": None,
            "claimed_at": None,
            "closed_at": None,
            "closed_by": None,
            "rating": None,
            "transcript": []
        }
        self._save_file('tickets')
        self._update_stats('tickets_created', ticket_type)
        return ticket_id
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        return self.data['tickets'].get(ticket_id)
    
    def get_user_tickets(self, user_id: str) -> Dict[str, Dict]:
        return {k: v for k, v in self.data['tickets'].items() 
                if v["user_id"] == user_id and v["status"] == "open"}
    
    def claim_ticket(self, ticket_id: str, staff_id: str) -> bool:
        if ticket_id in self.data['tickets']:
            self.data['tickets'][ticket_id]["claimed_by"] = staff_id
            self.data['tickets'][ticket_id]["claimed_at"] = datetime.now().isoformat()
            self._save_file('tickets')
            return True
        return False
    
    def close_ticket(self, ticket_id: str, closer_id: str) -> Optional[Dict]:
        if ticket_id in self.data['tickets']:
            ticket = self.data['tickets'][ticket_id]
            ticket["status"] = "closed"
            ticket["closed_by"] = closer_id
            ticket["closed_at"] = datetime.now().isoformat()
            self._save_file('tickets')
            self._update_stats('tickets_closed', ticket['type'])
            return ticket
        return None
    
    def add_transcript_message(self, ticket_id: str, author: str, content: str, attachments: List[str] = None):
        if ticket_id in self.data['tickets']:
            self.data['tickets'][ticket_id]["transcript"].append({
                "author": author,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "attachments": attachments or []
            })
            self._save_file('tickets')
    
    def add_rating(self, ticket_id: str, rating: int, feedback: str = None):
        if ticket_id in self.data['tickets']:
            self.data['tickets'][ticket_id]["rating"] = {
                "stars": rating,
                "feedback": feedback,
                "rated_at": datetime.now().isoformat()
            }
            self._save_file('tickets')
            
            # Save to ratings collection
            self.data['ratings'][ticket_id] = self.data['tickets'][ticket_id]["rating"]
            self._save_file('ratings')
            self._update_stats('ratings', str(rating))
    
    # Blacklist
    def is_blacklisted(self, user_id: str) -> bool:
        return user_id in self.data['blacklist']
    
    def blacklist_add(self, user_id: str, reason: str, by: str):
        self.data['blacklist'].append({
            "user_id": user_id,
            "reason": reason,
            "added_by": by,
            "added_at": datetime.now().isoformat()
        })
        self._save_file('blacklist')
    
    def blacklist_remove(self, user_id: str) -> bool:
        original_len = len(self.data['blacklist'])
        self.data['blacklist'] = [u for u in self.data['blacklist'] if u['user_id'] != user_id]
        if len(self.data['blacklist']) < original_len:
            self._save_file('blacklist')
            return True
        return False
    
    # Stats
    def _update_stats(self, metric: str, category: str):
        if metric not in self.data['stats']:
            self.data['stats'][metric] = {}
        if category not in self.data['stats'][metric]:
            self.data['stats'][metric][category] = 0
        self.data['stats'][metric][category] += 1
        self._save_file('stats')
    
    def get_stats(self) -> Dict:
        return self.data['stats']
    
    def get_average_rating(self) -> float:
        ratings = [r['stars'] for r in self.data['ratings'].values()]
        return sum(ratings) / len(ratings) if ratings else 0
