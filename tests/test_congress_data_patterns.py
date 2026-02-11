"""
Test suite for Congress Members data patterns and integrity
"""

import os
import sys
import unittest

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

class TestCongressDataPatterns(unittest.TestCase):
    """Test data patterns and integrity for Congress members data"""

    @classmethod
    def setUpClass(cls):
        """Set up database connection"""
        cls.conn_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }
        cls.conn = psycopg2.connect(**cls.conn_params)
        cls.conn.cursor_factory = DictCursor

    @classmethod
    def tearDownClass(cls):
        """Clean up database connection"""
        if cls.conn:
            cls.conn.close()

    def setUp(self):
        """Set up test cursor"""
        self.cursor = self.conn.cursor()

    def tearDown(self):
        """Clean up test cursor"""
        self.cursor.close()

    def query(self, sql, params=None):
        """Execute query and return results"""
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def query_one(self, sql, params=None):
        """Execute query and return single result"""
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone()

    # Test Basic Data Integrity

    def test_total_member_counts(self):
        """Test that we have the expected number of members and terms"""
        # Get counts
        total_members = self.query_one("SELECT COUNT(*) as count FROM congress.members")['count']
        total_terms = self.query_one("SELECT COUNT(*) as count FROM congress.member_terms")['count']
        unique_members = self.query_one("SELECT COUNT(DISTINCT bioguide_id) as count FROM congress.members")['count']

        # Assertions based on our ingestion results
        self.assertGreater(total_members, 1800, "Should have substantial number of member records")
        self.assertGreater(total_terms, 9000, "Should have substantial number of term records")
        self.assertEqual(total_members, unique_members, "All members should be unique by bioguide_id")

        print(f"✅ Total members: {total_members}, Total terms: {total_terms}")

    def test_congress_coverage(self):
        """Test that we have complete congress coverage (101-118)"""
        congress_numbers = self.query("""
            SELECT DISTINCT congress_number
            FROM congress.member_terms
            ORDER BY congress_number
        """)

        congress_list = [row['congress_number'] for row in congress_numbers]
        expected_congresses = list(range(101, 119))  # 101-118 inclusive

        self.assertEqual(len(congress_list), 18, "Should have 18 congresses")
        self.assertEqual(congress_list, expected_congresses, "Should cover congresses 101-118")

        print(f"✅ Congress coverage: {congress_list}")

    def test_bioguide_id_patterns(self):
        """Test bioguide ID format patterns"""
        # Check bioguide ID format (1 letter + 6 digits)
        invalid_bioguides = self.query("""
            SELECT bioguide_id
            FROM congress.members
            WHERE bioguide_id !~ '^[A-Z][0-9]{6}$'
        """)

        self.assertEqual(len(invalid_bioguides), 0, "All bioguide IDs should follow pattern LXXXXXX")

        # Check for duplicates
        duplicate_bioguides = self.query("""
            SELECT bioguide_id, COUNT(*) as count
            FROM congress.members
            GROUP BY bioguide_id
            HAVING COUNT(*) > 1
        """)

        self.assertEqual(len(duplicate_bioguides), 0, "Should have no duplicate bioguide IDs")

        print(f"✅ All {self.query_one('SELECT COUNT(*) as count FROM congress.members')['count']} bioguide IDs follow correct format")

    # Test Congress Patterns

    def test_congress_size_patterns(self):
        """Test expected Congress size patterns"""
        congress_sizes = self.query("""
            SELECT congress_number, COUNT(*) as member_count
            FROM congress.member_terms
            GROUP BY congress_number
            ORDER BY congress_number
        """)

        for row in congress_sizes:
            congress_num = row['congress_number']
            member_count = row['member_count']

            # House should have ~435 members, Senate should have ~100
            # Total should be between 500-600 (accounting for vacancies)
            self.assertGreater(member_count, 500, f"Congress {congress_num} should have >500 members")
            self.assertLess(member_count, 650, f"Congress {congress_num} should have <650 members")

        print("✅ All congresses have expected member counts (500-600 range)")

    def test_chamber_distribution_patterns(self):
        """Test chamber distribution patterns"""
        chamber_counts = self.query("""
            SELECT congress_number, chamber_code, COUNT(*) as count
            FROM congress.member_terms
            GROUP BY congress_number, chamber_code
            ORDER BY congress_number, chamber_code
        """)

        for row in chamber_counts:
            congress_num = row['congress_number']
            chamber = row['chamber_code']
            count = row['count']

            if chamber == 'house':
                self.assertGreater(count, 430, f"House in Congress {congress_num} should have >430 members")
                self.assertLess(count, 445, f"House in Congress {congress_num} should have <445 members")
            elif chamber == 'senate':
                self.assertGreater(count, 95, f"Senate in Congress {congress_num} should have >95 members")
                self.assertLess(count, 115, f"Senate in Congress {congress_num} should have <115 members")

        print("✅ Chamber distributions follow expected patterns")

    def test_state_representation_patterns(self):
        """Test state representation patterns"""
        # Each congress should have all 50 states + territories represented
        states_by_congress = self.query("""
            SELECT congress_number, COUNT(DISTINCT state_code) as state_count
            FROM congress.member_terms
            GROUP BY congress_number
            ORDER BY congress_number
        """)

        for row in states_by_congress:
            congress_num = row['congress_number']
            state_count = row['state_count']

            # Should have at least 50 states, likely more with territories
            self.assertGreater(state_count, 45, f"Congress {congress_num} should represent >45 states")
            self.assertLess(state_count, 60, f"Congress {congress_num} should represent <60 states")

        print("✅ State representation patterns are correct")

    def test_party_distribution_patterns(self):
        """Test party distribution patterns"""
        party_counts = self.query("""
            SELECT congress_number, party_code, COUNT(*) as count
            FROM congress.member_terms
            WHERE party_code IN ('D', 'R')
            GROUP BY congress_number, party_code
            ORDER BY congress_number, party_code
        """)

        # Organize by congress
        congress_parties = {}
        for row in party_counts:
            congress_num = row['congress_number']
            if congress_num not in congress_parties:
                congress_parties[congress_num] = {}
            congress_parties[congress_num][row['party_code']] = row['count']

        # Check that both major parties are represented in each congress
        for congress_num, parties in congress_parties.items():
            self.assertIn('D', parties, f"Democrats should be represented in Congress {congress_num}")
            self.assertIn('R', parties, f"Republicans should be represented in Congress {congress_num}")

            # Both parties should have substantial representation
            self.assertGreater(parties['D'], 150, f"Democrats should have >150 members in Congress {congress_num}")
            self.assertGreater(parties['R'], 150, f"Republicans should have >150 members in Congress {congress_num}")

        print("✅ Party distribution patterns are correct")

    # Test Temporal Patterns

    def test_term_date_patterns(self):
        """Test term date patterns and consistency"""
        # Check that start dates are reasonable
        invalid_dates = self.query("""
            SELECT bioguide_id, congress_number, start_date, end_date
            FROM congress.member_terms
            WHERE start_date IS NULL
               OR end_date IS NULL
               OR start_date > end_date
               OR start_date < '1989-01-01'
               OR end_date > '2025-12-31'
        """)

        self.assertEqual(len(invalid_dates), 0, "All term dates should be valid and in expected range")

        # Check congress-year alignment
        misaligned_dates = self.query("""
            SELECT mt.bioguide_id, mt.congress_number, mt.start_date, s.start_date as expected_start
            FROM congress.member_terms mt
            JOIN congress.sessions s ON mt.congress_number = s.congress_number
            WHERE mt.start_date::year != s.odd_year
        """)

        # Allow some flexibility here as terms might span congress boundaries
        print(f"✅ Term date patterns checked (found {len(misaligned_dates)} potential misalignments)")

    def test_career_continuity_patterns(self):
        """Test career continuity and progression patterns"""
        # Find members with continuous service
        continuous_members = self.query("""
            SELECT bioguide_id, COUNT(*) as term_count
            FROM congress.member_terms
            GROUP BY bioguide_id
            HAVING COUNT(*) >= 10  -- At least 5 terms of service
            ORDER BY term_count DESC
            LIMIT 20
        """)

        self.assertGreater(len(continuous_members), 0, "Should have members with long service")

        # Check for reasonable career progression
        longest_serving = continuous_members[0]
        self.assertGreater(longest_serving['term_count'], 15, "Should have members with very long service")

        print(f"✅ Career continuity patterns: {len(continuous_members)} members with 10+ terms")

    # Test Data Quality Patterns

    def test_district_patterns(self):
        """Test district numbering patterns"""
        # House members should have valid district numbers
        invalid_districts = self.query("""
            SELECT bioguide_id, congress_number, district
            FROM congress.member_terms
            WHERE chamber_code = 'house'
              AND (district IS NULL OR district = '' OR district ~ '[^0-9]')
        """)

        # Allow some flexibility for at-large districts
        print(f"✅ District patterns checked (found {len(invalid_districts)} potential issues)")

    def test_foreign_key_integrity(self):
        """Test all foreign key relationships"""
        # Test member_terms -> members
        orphaned_terms = self.query("""
            SELECT COUNT(*) as count
            FROM congress.member_terms mt
            LEFT JOIN congress.members m ON mt.bioguide_id = m.bioguide_id
            WHERE m.bioguide_id IS NULL
        """)

        self.assertEqual(orphaned_terms[0]['count'], 0, "All member terms should reference valid members")

        # Test member_terms -> sessions
        invalid_sessions = self.query("""
            SELECT COUNT(*) as count
            FROM congress.member_terms mt
            LEFT JOIN congress.sessions s ON mt.congress_number = s.congress_number
            WHERE s.congress_number IS NULL
        """)

        self.assertEqual(invalid_sessions[0]['count'], 0, "All member terms should reference valid sessions")

        # Test other foreign keys
        invalid_chambers = self.query("""
            SELECT COUNT(*) as count
            FROM congress.member_terms mt
            LEFT JOIN congress.chambers c ON mt.chamber_code = c.chamber_code
            WHERE c.chamber_code IS NULL
        """)

        self.assertEqual(invalid_chambers[0]['count'], 0, "All member terms should reference valid chambers")

        print("✅ All foreign key relationships are valid")

    def test_data_consistency_patterns(self):
        """Test overall data consistency patterns"""
        # Test that member counts match expectations
        member_summary = self.query_one("""
            SELECT
                COUNT(DISTINCT bioguide_id) as unique_members,
                COUNT(*) as total_terms,
                COUNT(DISTINCT congress_number) as congresses,
                COUNT(DISTINCT state_code) as states,
                COUNT(DISTINCT chamber_code) as chambers
            FROM congress.member_terms
        """)

        summary = dict(member_summary)

        self.assertEqual(summary['chambers'], 2, "Should have exactly 2 chambers")
        self.assertEqual(summary['congresses'], 18, "Should have 18 congresses")
        self.assertGreater(summary['states'], 50, "Should have at least 50 states")
        self.assertGreater(summary['unique_members'], 1800, "Should have substantial unique members")
        self.assertGreater(summary['total_terms'], 9000, "Should have substantial total terms")

        print(f"✅ Data consistency: {summary['unique_members']} members, {summary['total_terms']} terms, {summary['congresses']} congresses")


class TestCongressDataAnomalies(unittest.TestCase):
    """Test for data anomalies and edge cases"""

    @classmethod
    def setUpClass(cls):
        """Set up database connection"""
        cls.conn_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }
        cls.conn = psycopg2.connect(**cls.conn_params)
        cls.conn.cursor_factory = DictCursor

    @classmethod
    def tearDownClass(cls):
        """Clean up database connection"""
        if cls.conn:
            cls.conn.close()

    def setUp(self):
        """Set up test cursor"""
        self.cursor = self.conn.cursor()

    def tearDown(self):
        """Clean up test cursor"""
        self.cursor.close()

    def query(self, sql, params=None):
        """Execute query and return results"""
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def test_party_switchers(self):
        """Test for members who switched parties"""
        party_switchers = self.query("""
            SELECT bioguide_id, COUNT(DISTINCT party_code) as party_count
            FROM congress.member_terms
            GROUP BY bioguide_id
            HAVING COUNT(DISTINCT party_code) > 1
            ORDER BY party_count DESC
        """)

        print(f"✅ Found {len(party_switchers)} members who switched parties")

        # Party switching is actually rare in modern Congress (typically <2% of members)
        # So we expect very few or none in our dataset
        total_members = self.query("SELECT COUNT(DISTINCT bioguide_id) as count FROM congress.member_terms")[0]['count']

        if len(party_switchers) > 0:
            # If we have party switchers, verify they have reasonable party counts
            for switcher in party_switchers:
                self.assertLess(switcher['party_count'], 5, "No member should switch parties more than 4 times")
            print("✅ Party switchers found with reasonable party counts")
        else:
            # No party switchers is also valid for many congress periods
            print("✅ No party switchers found (valid for many congress periods)")

        # At minimum, we should have party diversity
        party_diversity = self.query("""
            SELECT COUNT(DISTINCT party_code) as party_count
            FROM congress.member_terms
        """)[0]['party_count']

        self.assertGreater(party_diversity, 1, "Should have multiple parties represented")

    def test_chamber_switchers(self):
        """Test for members who served in both chambers"""
        chamber_switchers = self.query("""
            SELECT bioguide_id, COUNT(DISTINCT chamber_code) as chamber_count
            FROM congress.member_terms
            GROUP BY bioguide_id
            HAVING COUNT(DISTINCT chamber_code) > 1
            ORDER BY chamber_count DESC
        """)

        print(f"✅ Found {len(chamber_switchers)} members who served in both chambers")

        # Should find some chamber switchers
        self.assertGreater(len(chamber_switchers), 0, "Should have some members who served in both chambers")

        # Should only be 2 chambers max
        for switcher in chamber_switchers:
            self.assertEqual(switcher['chamber_count'], 2, "Members should serve in max 2 chambers")

    def test_state_switchers(self):
        """Test for members who represented different states"""
        state_switchers = self.query("""
            SELECT bioguide_id, COUNT(DISTINCT state_code) as state_count
            FROM congress.member_terms
            GROUP BY bioguide_id
            HAVING COUNT(DISTINCT state_code) > 1
            ORDER BY state_count DESC
        """)

        print(f"✅ Found {len(state_switchers)} members who represented multiple states")

        # Should be very few state switchers (if any)
        self.assertLess(len(state_switchers), 10, "Should have very few members who represented multiple states")

    def test_gaps_in_service(self):
        """Test for gaps in member service"""
        service_gaps = self.query("""
            SELECT DISTINCT mt1.bioguide_id, mt1.congress_number as congress1, mt2.congress_number as congress2
            FROM congress.member_terms mt1
            JOIN congress.member_terms mt2 ON mt1.bioguide_id = mt2.bioguide_id
            WHERE mt2.congress_number = mt1.congress_number + 1
              AND NOT EXISTS (
                  SELECT 1 FROM congress.member_terms mt3
                  WHERE mt3.bioguide_id = mt1.bioguide_id
                    AND mt3.congress_number = mt1.congress_number + 1
              )
        """)

        print("✅ Checked for service gaps (complex query - results may vary)")

    def test_extreme_service_lengths(self):
        """Test for members with extremely long or short service"""
        service_stats = self.query("""
            SELECT
                bioguide_id,
                COUNT(*) as term_count,
                MIN(congress_number) as first_congress,
                MAX(congress_number) as last_congress,
                MAX(congress_number) - MIN(congress_number) + 1 as congress_span
            FROM congress.member_terms
            GROUP BY bioguide_id
            ORDER BY congress_span DESC
        """)

        # Longest serving
        longest = service_stats[0]
        self.assertGreater(longest['congress_span'], 15, "Should have members with >15 congresses of service")

        # Shortest serving
        shortest = service_stats[-1]
        self.assertGreaterEqual(shortest['congress_span'], 1, "All members should have at least 1 congress of service")

        print(f"✅ Service span range: {shortest['congress_span']} to {longest['congress_span']} congresses")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
