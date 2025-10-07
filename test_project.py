"""
Unit tests for Mango: The Virtual Lovebird
Tests all core Tamagotchi functionality and game mechanics.
"""

import pytest
import sqlite3
import tempfile
import os
import shutil
from datetime import datetime, timedelta
import time
from unittest.mock import patch, MagicMock
import sys

# Add the project directory to the path so we can import project.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project import MangoTamagotchi, GameState

class TestMangoTamagotchi:
    """Test class for MangoTamagotchi functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_mango.db")
        
        # Create the database with schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        schema = """
        CREATE TABLE IF NOT EXISTS mango_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hunger INTEGER NOT NULL CHECK(hunger BETWEEN 0 AND 100),
            happiness INTEGER NOT NULL CHECK(happiness BETWEEN 0 AND 100),
            cleanliness INTEGER NOT NULL CHECK(cleanliness BETWEEN 0 AND 100),
            energy INTEGER NOT NULL CHECK(energy BETWEEN 0 AND 100),
            health INTEGER NOT NULL CHECK(health BETWEEN 0 AND 100),
            age INTEGER NOT NULL DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER NOT NULL,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.executescript(schema)
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mango_game(self, temp_db):
        """Create a MangoTamagotchi instance with temporary database."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.font.Font'), \
             patch('pygame.time.Clock'), \
             patch('pygame.event.get', return_value=[]), \
             patch('pygame.mouse.get_pos', return_value=(0, 0)), \
             patch('pygame.mouse.get_pressed', return_value=(False, False, False)):
            
            game = MangoTamagotchi()
            game.db_path = temp_db
            game.screen = MagicMock()
            game.clock = MagicMock()
            game.font = MagicMock()
            game.small_font = MagicMock()
            
            return game
    
    def test_initial_state(self, mango_game):
        """Test that Mango starts with proper initial stats."""
        initial_state = {
            'hunger': 80,
            'happiness': 70,
            'cleanliness': 60,
            'energy': 90,
            'health': 100,
            'age': 0
        }
        
        mango_game.mango_state = initial_state
        mango_game.save_state()
        
        # Load state and verify
        loaded_state = mango_game.load_state()
        assert loaded_state is not None
        assert loaded_state['hunger'] == 80
        assert loaded_state['happiness'] == 70
        assert loaded_state['cleanliness'] == 60
        assert loaded_state['energy'] == 90
        assert loaded_state['health'] == 100
        assert loaded_state['age'] == 0
    
    def test_feed_mango(self, mango_game):
        """Test feeding Mango increases hunger and happiness."""
        mango_game.mango_state['hunger'] = 50
        mango_game.mango_state['happiness'] = 60
        
        result = mango_game.feed_mango()
        
        assert result is True
        assert mango_game.mango_state['hunger'] == 75  # 50 + 25
        assert mango_game.mango_state['happiness'] == 65  # 60 + 5
    
    def test_feed_mango_max_hunger(self, mango_game):
        """Test feeding Mango doesn't exceed max hunger."""
        mango_game.mango_state['hunger'] = 95
        mango_game.mango_state['happiness'] = 60
        
        result = mango_game.feed_mango()
        
        assert result is True
        assert mango_game.mango_state['hunger'] == 100  # Capped at 100
        assert mango_game.mango_state['happiness'] == 65  # 60 + 5
    
    def test_bathe_mango(self, mango_game):
        """Test bathing Mango increases cleanliness and happiness."""
        mango_game.mango_state['cleanliness'] = 40
        mango_game.mango_state['happiness'] = 50
        
        result = mango_game.bathe_mango()
        
        assert result is True
        assert mango_game.mango_state['cleanliness'] == 70  # 40 + 30
        assert mango_game.mango_state['happiness'] == 60  # 50 + 10
    
    def test_bathe_mango_max_cleanliness(self, mango_game):
        """Test bathing Mango doesn't exceed max cleanliness."""
        mango_game.mango_state['cleanliness'] = 90
        mango_game.mango_state['happiness'] = 50
        
        result = mango_game.bathe_mango()
        
        assert result is True
        assert mango_game.mango_state['cleanliness'] == 100  # Capped at 100
        assert mango_game.mango_state['happiness'] == 60  # 50 + 10
    
    def test_play_with_mango(self, mango_game):
        """Test playing with Mango increases happiness but decreases energy."""
        mango_game.mango_state['happiness'] = 50
        mango_game.mango_state['energy'] = 80
        
        result = mango_game.play_with_mango()
        
        assert result is True
        assert mango_game.mango_state['happiness'] == 70  # 50 + 20
        assert mango_game.mango_state['energy'] == 65  # 80 - 15
    
    def test_play_with_mango_low_energy(self, mango_game):
        """Test playing with Mango fails when energy is too low."""
        mango_game.mango_state['happiness'] = 50
        mango_game.mango_state['energy'] = 5  # Too low
        
        result = mango_game.play_with_mango()
        
        assert result is False
        assert mango_game.mango_state['happiness'] == 50  # Unchanged
        assert mango_game.mango_state['energy'] == 5  # Unchanged
    
    def test_rest_mango(self, mango_game):
        """Test resting Mango increases energy."""
        mango_game.mango_state['energy'] = 60
        
        result = mango_game.rest_mango()
        
        assert result is True
        assert mango_game.mango_state['energy'] == 90  # 60 + 30
    
    def test_rest_mango_max_energy(self, mango_game):
        """Test resting Mango doesn't exceed max energy."""
        mango_game.mango_state['energy'] = 95
        
        result = mango_game.rest_mango()
        
        assert result is True
        assert mango_game.mango_state['energy'] == 100  # Capped at 100
    
    def test_give_medicine_when_sick(self, mango_game):
        """Test giving medicine when Mango is sick."""
        mango_game.is_sick = True
        mango_game.mango_state['health'] = 50
        
        result = mango_game.give_medicine()
        
        assert result is True
        assert mango_game.mango_state['health'] == 100  # fully healed
        assert mango_game.is_sick is False
    
    def test_give_medicine_when_not_sick(self, mango_game):
        """Test giving medicine when Mango is not sick."""
        mango_game.is_sick = False
        mango_game.mango_state['health'] = 50
        
        result = mango_game.give_medicine()

        # Medicine is now allowed regardless of sickness and fully restores health
        assert result is True
        assert mango_game.mango_state['health'] == 100  # fully healed
        assert mango_game.is_sick is False
    
    def test_discipline_reduces_misbehavior(self, mango_game):
        """Test disciplining Mango reduces misbehavior count."""
        mango_game.misbehavior_count = 3
        mango_game.mango_state['happiness'] = 60
        
        result = mango_game.discipline()
        
        assert result is True
        assert mango_game.misbehavior_count == 2  # 3 - 1
        assert mango_game.mango_state['happiness'] == 55  # 60 - 5
    
    def test_discipline_no_misbehavior(self, mango_game):
        """Test disciplining Mango when no misbehavior."""
        mango_game.misbehavior_count = 0
        mango_game.mango_state['happiness'] = 60
        
        result = mango_game.discipline()
        
        assert result is False
        assert mango_game.misbehavior_count == 0  # Unchanged
        assert mango_game.mango_state['happiness'] == 60  # Unchanged
    
    def test_age_mango(self, mango_game):
        """Test aging Mango based on time passed."""
        mango_game.mango_state['age'] = 5
        mango_game.mango_state['last_updated'] = (datetime.now() - timedelta(hours=25)).isoformat()
        
        mango_game.age_mango()
        
        assert mango_game.mango_state['age'] == 6  # 5 + 1
    
    def test_age_mango_not_enough_time(self, mango_game):
        """Test aging Mango when not enough time has passed."""
        mango_game.mango_state['age'] = 5
        mango_game.mango_state['last_updated'] = (datetime.now() - timedelta(hours=12)).isoformat()
        
        mango_game.age_mango()
        
        assert mango_game.mango_state['age'] == 5  # Unchanged
    
    def test_get_mango_mood_happy(self, mango_game):
        """Test getting Mango's mood when happy."""
        mango_game.mango_state['happiness'] = 80
        mango_game.mango_state['cleanliness'] = 70
        mango_game.mango_state['energy'] = 80
        mango_game.is_sick = False
        
        mood = mango_game.get_mango_mood()
        assert mood == "happy"
    
    def test_get_mango_mood_sad(self, mango_game):
        """Test getting Mango's mood when sad."""
        mango_game.mango_state['happiness'] = 20
        mango_game.mango_state['cleanliness'] = 70
        mango_game.mango_state['energy'] = 80
        mango_game.is_sick = False
        
        mood = mango_game.get_mango_mood()
        assert mood == "sad"
    
    def test_get_mango_mood_tired(self, mango_game):
        """Test getting Mango's mood when tired."""
        mango_game.mango_state['happiness'] = 50
        mango_game.mango_state['cleanliness'] = 70
        mango_game.mango_state['energy'] = 15
        mango_game.is_sick = False
        
        mood = mango_game.get_mango_mood()
        assert mood == "tired"
    
    def test_get_mango_mood_dirty(self, mango_game):
        """Test getting Mango's mood when dirty."""
        mango_game.mango_state['happiness'] = 50
        mango_game.mango_state['cleanliness'] = 20
        mango_game.mango_state['energy'] = 80
        mango_game.is_sick = False
        
        mood = mango_game.get_mango_mood()
        assert mood == "dirty"
    
    def test_get_mango_mood_sick(self, mango_game):
        """Test getting Mango's mood when sick."""
        mango_game.mango_state['happiness'] = 50
        mango_game.mango_state['cleanliness'] = 70
        mango_game.mango_state['energy'] = 80
        mango_game.is_sick = True
        
        mood = mango_game.get_mango_mood()
        assert mood == "sick"
    
    def test_is_game_over_true(self, mango_game):
        """Test game over when health is 0."""
        mango_game.mango_state['health'] = 0
        
        result = mango_game.is_game_over()
        assert result is True
    
    def test_is_game_over_false(self, mango_game):
        """Test game not over when health > 0."""
        mango_game.mango_state['health'] = 50
        
        result = mango_game.is_game_over()
        assert result is False
    
    def test_restart_game(self, mango_game):
        """Test restarting the game with new Mango."""
        # Set some custom state
        mango_game.mango_state['hunger'] = 10
        mango_game.mango_state['health'] = 0
        mango_game.is_sick = True
        mango_game.misbehavior_count = 5
        
        mango_game.restart_game()
        
        assert mango_game.mango_state['hunger'] == 80
        assert mango_game.mango_state['happiness'] == 70
        assert mango_game.mango_state['cleanliness'] == 60
        assert mango_game.mango_state['energy'] == 90
        assert mango_game.mango_state['health'] == 100
        assert mango_game.mango_state['age'] == 0
        assert mango_game.is_sick is False
        assert mango_game.misbehavior_count == 0
    
    def test_save_and_get_score(self, mango_game):
        """Test saving and retrieving scores."""
        # Save some scores
        mango_game.save_score(100)
        mango_game.save_score(150)
        mango_game.save_score(75)
        
        high_score = mango_game.get_high_score()
        assert high_score == 150
    
    def test_save_score_empty_database(self, mango_game):
        """Test getting high score from empty database."""
        high_score = mango_game.get_high_score()
        assert high_score == 0
    
    def test_stat_constraints(self, mango_game):
        """Test that stats are properly constrained between 0 and 100."""
        # Test feeding at max hunger - should return False since can't increase
        mango_game.mango_state['hunger'] = 100
        result = mango_game.feed_mango()
        assert result is False  # Should return False when already at max
        assert mango_game.mango_state['hunger'] == 100  # Should remain at 100
        
        # Test bathing at max cleanliness - should return False since can't increase
        mango_game.mango_state['cleanliness'] = 100
        result = mango_game.bathe_mango()
        assert result is False  # Should return False when already at max
        assert mango_game.mango_state['cleanliness'] == 100  # Should remain at 100
        
        # Test resting at max energy - should return False since can't increase
        mango_game.mango_state['energy'] = 100
        result = mango_game.rest_mango()
        assert result is False  # Should return False when already at max
        assert mango_game.mango_state['energy'] == 100  # Should remain at 100
    
    def test_stat_decay_over_time(self, mango_game):
        """Test that stats decay over time."""
        mango_game.mango_state['hunger'] = 50
        mango_game.mango_state['happiness'] = 60
        mango_game.mango_state['cleanliness'] = 70
        mango_game.mango_state['energy'] = 80
        mango_game.last_stat_update = time.time() - 35  # 35 seconds ago
        
        mango_game.update_stats()
        
        # Stats should have decayed
        assert mango_game.mango_state['hunger'] < 50
        assert mango_game.mango_state['happiness'] < 60
        assert mango_game.mango_state['cleanliness'] < 70
        assert mango_game.mango_state['energy'] < 80
    
    def test_health_decay_low_stats(self, mango_game):
        """Test that health decays when other stats are too low."""
        mango_game.mango_state['hunger'] = 5  # Very low
        mango_game.mango_state['cleanliness'] = 8  # Very low
        mango_game.mango_state['energy'] = 12  # Very low
        mango_game.mango_state['health'] = 50
        mango_game.last_stat_update = time.time() - 35  # 35 seconds ago
        
        initial_health = mango_game.mango_state['health']
        mango_game.update_stats()
        
        # Health should have decreased
        assert mango_game.mango_state['health'] < initial_health
    
    def test_database_constraints(self, mango_game):
        """Test database constraints for stat values."""
        # Test that database rejects invalid stat values
        conn = sqlite3.connect(mango_game.db_path)
        cursor = conn.cursor()
        
        # This should raise an IntegrityError due to CHECK constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO mango_state 
                (hunger, happiness, cleanliness, energy, health, age)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (150, 50, 50, 50, 50, 0))  # hunger > 100
        
        conn.close()
    
    def test_random_events(self, mango_game):
        """Test random event system."""
        mango_game.last_random_event = time.time() - 130  # 130 seconds ago
        mango_game.is_sick = False
        mango_game.misbehavior_count = 0
        
        # Mock random choice to ensure we get an event
        with patch('random.random', return_value=0.1), \
             patch('random.choice', return_value='sick'):
            
            mango_game.check_random_events()
            
            # Should trigger a random event
            assert mango_game.is_sick is True
    
    def test_day_night_cycle(self, mango_game):
        """Test day/night cycle detection."""
        # Test night time (2 AM)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 2
            mango_game.current_hour = 2
            mango_game.is_night = mango_game.current_hour < 6 or mango_game.current_hour > 18
            assert mango_game.is_night is True
        
        # Test day time (2 PM)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 14
            mango_game.current_hour = 14
            mango_game.is_night = mango_game.current_hour < 6 or mango_game.current_hour > 18
            assert mango_game.is_night is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
