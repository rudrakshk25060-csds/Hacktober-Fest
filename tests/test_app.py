import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main


class JobiFCTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp.name) / "matches.json"
        self.path_patch = patch.object(main, "DATA_FILE", self.data_path)
        self.path_patch.start()
        self.client = TestClient(main.app)

    def tearDown(self):
        self.path_patch.stop()
        self.temp.cleanup()

    def test_home_and_empty_analysis(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/api/analysis").json()["matches"], 0)

    def test_log_match_calculates_metrics_and_rejects_impossible_stats(self):
        payload = {"opponent": "Northside FC", "position": "Midfielder", "minutes": 90, "goals": 1, "assists": 0,
                   "shots": 2, "shots_on_target": 1, "passes_attempted": 20, "passes_completed": 15, "tackles": 3}
        response = self.client.post("/api/matches", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["analysis"]["latest_metrics"]["pass_accuracy"], 75)
        payload["passes_completed"] = 21
        self.assertEqual(self.client.post("/api/matches", json=payload).status_code, 422)

    def test_chat_reports_gemma_or_fallback_source(self):
        payload = {"position": "Forward", "minutes": 90, "goals": 0, "assists": 0, "shots": 1, "shots_on_target": 0,
                   "passes_attempted": 10, "passes_completed": 8, "tackles": 1}
        self.client.post("/api/matches", json=payload)
        with patch.object(main, "gemma", return_value=None):
            response = self.client.post("/api/coach", json={"question": "What should I work on?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("fallback", response.json()["source"].lower())

    def test_chat_uses_gemma_and_receives_the_selected_focus(self):
        payload = {"position": "Forward", "minutes": 90, "goals": 1, "assists": 0, "shots": 5, "shots_on_target": 1,
                   "passes_attempted": 25, "passes_completed": 18, "tackles": 2}
        self.client.post("/api/matches", json=payload)
        focus = main.insights(main.load_matches())["focus"]
        with patch.object(main, "gemma", return_value="Try 3 sets of controlled shots aimed at the corners.") as model:
            response = self.client.post("/api/coach", json={"question": "Give me a drill"})
        self.assertEqual(response.json()["source"], "Gemma")
        self.assertIn(f"The one next focus to use is: {focus}", model.call_args.args[0])

    def test_conflicting_gemma_advice_is_replaced_with_focus_specific_drill(self):
        payload = {"position": "Forward", "minutes": 90, "goals": 1, "assists": 0, "shots": 5, "shots_on_target": 1,
                   "passes_attempted": 25, "passes_completed": 18, "tackles": 2}
        self.client.post("/api/matches", json=payload)
        with patch.object(main, "gemma", return_value="Focus on passing combinations and passing accuracy."):
            response = self.client.post("/api/coach", json={"question": "What drill should I do?"})
        self.assertIn("fallback", response.json()["source"].lower())
        self.assertIn("finishing", response.json()["answer"])
        self.assertNotIn("passing", response.json()["answer"].lower())

    def test_csv_import(self):
        csv_data = b"player,date,opponent,position,minutes,goals,assists,shots,shots_on_target,passes_attempted,passes_completed,tackles\nJobi Anand,2026-10-03,Northside FC,Midfielder,90,0,1,2,1,20,17,3\n"
        response = self.client.post("/api/import", files={"file": ("matches.csv", csv_data, "text/csv")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["imported"], 1)


if __name__ == "__main__":
    unittest.main()
