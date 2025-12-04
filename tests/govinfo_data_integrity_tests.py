#!/usr/bin/env python3
"""
Tests for GovInfo data integrity and duplicate detection
Ensures no gaps or duplicates in ingestion process
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Set

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats


class TestGovInfoDataIntegrity:
    """Test suite for data integrity validation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.ingestor = FixedGovInfoIngestor()
        self.ingestor.logger = mock.MagicMock()

    def get_mock_db_connection(self):
        """Create mock database connection"""
        conn = mock.MagicMock()
        cursor = mock.MagicMock()
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = None
        return conn, cursor

    def test_no_duplicate_bills_insertion(self):
        """Test that duplicate bills are not inserted"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        test_bills = [
            {'packageId': 'BILLS-118hr1-2023-01-01', 'dateIssued': '2023-01-01'},
            {'packageId': 'BILLS-118hr1-2023-01-01', 'dateIssued': '2023-01-01'},
            {'packageId': 'BILLS-118hr2-2023-01-01', 'dateIssued': '2023-01-01'},
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            inserted_data = []

            def mock_execute_values(query, values):
                inserted_data.extend(values)

            with patch('psycopg2.extras.execute_values', side_effect=mock_execute_values):
                result = self.ingestor.insert_batch(config, test_bills)

                assert len(inserted_data) == 2
                assert result == 2

    def test_no_duplicate_votes_insertion(self):
        """Test that duplicate votes are not inserted"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118
        )

        test_votes = [
            {'rollId': 'vote-2023-001', 'date': '2023-01-01'},
            {'rollId': 'vote-2023-001', 'date': '2023-01-01'},
            {'rollId': 'vote-2023-002', 'date': '2023-01-02'},
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            inserted_data = []

            def mock_execute_values(query, values):
                inserted_data.extend(values)

            with patch('psycopg2.extras.execute_values', side_effect=mock_execute_values):
                result = self.ingestor.insert_batch(config, test_votes)

                assert len(inserted_data) == 2
                assert result == 2

    def test_data_gap_detection_in_offset_sequence(self):
        """Test detection of gaps in offset sequence during ingestion"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        expected_offsets = [0, 100, 200, 300, 400]
        actual_offsets = []

        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(0, 100)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100, 195)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(195, 300)]},
            {'packages': []},
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            offset = 0
            for items_batch in self.ingestor.paginate_api_response(config, offset):
                actual_offsets.append(offset)
                offset += len(items_batch)

            assert len(actual_offsets) == len(expected_offsets)
            for expected, actual in zip(expected_offsets, actual_offsets):
                assert expected == actual

    def test_data_continuity_across_checkpoints(self):
        """Test data continuity when resuming from checkpoint"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            enable_checkpoint=True,
            resume_from_checkpoint=True
        )

        with patch.object(self.ingestor, 'get_checkpoint', return_value=(150, False)):
            conn, cursor = self.get_mock_db_connection()
            cursor.fetchone.return_value = (150,)

            api_responses = [
                {'packages': [{'packageId': f'bill-{i}'} for i in range(150, 250)]},
                {'packages': []}
            ]

            with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
                 patch.object(self.ingestor, 'get_db_connection', return_value=conn):

                mock_fetch.side_effect = api_responses

                offset, is_completed = self.ingestor.get_checkpoint(config)
                assert offset == 150

                batches = list(self.ingestor.paginate_api_response(config, 150))

                assert len(batches) == 1
                assert len(batches[0]) == 100

    def test_bill_data_normalization_integrity(self):
        """Test that bill data normalization preserves integrity"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        test_bill = {
            'packageId': 'BILLS-118hr1234-2023-05-15',
            'dateIssued': '2023-05-15T12:00:00Z',
            'lastModified': '2023-05-16T10:30:00Z',
            'download': [{'url': 'https://example.com/bill.pdf'}]
        }

        normalized = self.ingestor.normalize_bill_data(test_bill)

        assert normalized['package_id'] == 'BILLS-118hr1234-2023-05-15'
        assert normalized['congress_number'] == 118
        assert normalized['bill_type'] == 'hr'
        assert normalized['bill_number'] == '1234'
        assert normalized['date_issued'] == '2023-05-15'
        assert normalized['last_modified'] == '2023-05-16'
        assert 'download' in normalized['downloads']

    def test_vote_data_normalization_integrity(self):
        """Test that vote data normalization preserves integrity"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118
        )

        test_vote = {
            'rollId': 'vote-2023-001',
            'date': '2023-05-15T14:30:00Z',
            'chamber': 'Senate',
            'session': '1st Session',
            'rollNumber': '150',
            'question': 'On the motion to proceed',
            'type': 'On Motion to Proceed',
            'subject': 'Healthcare Bill',
            'byMember': [
                {'memberId': 'M001', 'vote': 'Yes'},
                {'memberId': 'M002', 'vote': 'No'}
            ]
        }

        normalized = self.ingestor.normalize_vote_data(test_vote)

        assert normalized['roll_id'] == 'vote-2023-001'
        assert normalized['congress_number'] == 118
        assert normalized['chamber_code'] == 'Senate'
        assert normalized['session_id'] == '1st Session'
        assert normalized['vote_number'] == '150'
        assert normalized['vote_question'] == 'On the motion to proceed'
        assert normalized['vote_type'] == 'On Motion to Proceed'
        assert normalized['subject'] == 'Healthcare Bill'

        metadata = json.loads(normalized['metadata'])
        assert len(metadata) == 2
        assert metadata[0]['memberId'] == 'M001'

    def test_member_data_normalization_integrity(self):
        """Test that member data normalization preserves integrity"""
        config = IngestionConfig(
            data_type=DataType.MEMBERS,
            congress=118
        )

        test_member = {
            'memberId': 'M001',
            'bioguideId': 'D000123',
            'name': {
                'first': 'John',
                'last': 'Doe',
                'middle': 'Smith',
                'fullName': 'John Smith Doe',
                'preferredName': 'John'
            },
            'birthDate': '1975-03-15',
            'deathDate': None,
            'gender': 'M',
            'party': 'Democrat',
            'state': 'CA',
            'district': '1',
            'url': 'https://example.com/johndoe',
            'twitter': '@johndoe',
            'youtube': 'johndoe_channel',
            'facebook': 'johndoe',
            'biography': 'Biography text',
            'photoUrl': 'https://example.com/photo.jpg'
        }

        normalized = self.ingestor.normalize_member_data(test_member)

        assert normalized['member_id'] == 'M001'
        assert normalized['bioguide_id'] == 'D000123'
        assert normalized['first_name'] == 'John'
        assert normalized['middle_name'] == 'Smith'
        assert normalized['last_name'] == 'Doe'
        assert normalized['full_name'] == 'John Smith Doe'
        assert normalized['preferred_name'] == 'John'
        assert normalized['birthday'] == '1975-03-15'
        assert normalized['death_date'] is None
        assert normalized['gender'] == 'M'
        assert normalized['party_code'] == 'Democrat'
        assert normalized['state'] == 'CA'
        assert normalized['district'] == '1'
        assert normalized['url'] == 'https://example.com/johndoe'
        assert normalized['twitter_handle'] == '@johndoe'
        assert normalized['youtube_handle'] == 'johndoe_channel'
        assert normalized['facebook_handle'] == 'johndoe'
        assert normalized['biography_text'] == 'Biography text'
        assert normalized['photo_url'] == 'https://example.com/photo.jpg'

    def test_invalid_data_handling(self):
        """Test that invalid data is filtered out during normalization"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        test_bills = [
            {'packageId': 'valid-bill-1', 'dateIssued': '2023-01-01'},
            {'packageId': '', 'dateIssued': '2023-01-01'},
            {'dateIssued': '2023-01-01'},
            {'packageId': 'valid-bill-2', 'dateIssued': '2023-01-01'},
        ]

        normalized_bills = []
        for bill_data in test_bills:
            normalized = self.ingestor.normalize_bill_data(bill_data)
            if normalized:
                normalized_bills.append(normalized)

        assert len(normalized_bills) == 2
        assert normalized_bills[0]['package_id'] == 'valid-bill-1'
        assert normalized_bills[1]['package_id'] == 'valid-bill-2'

    def test_date_parsing_edge_cases(self):
        """Test date parsing handles various formats correctly"""
        test_dates = [
            ('2023-05-15T12:00:00Z', '2023-05-15'),
            ('2023-05-15', '2023-05-15'),
            ('2023/05/15', '2023-05-15'),
            ('05/15/2023', '2023-05-15'),
            ('', None),
            (None, None),
            ('invalid-date', None),
        ]

        for date_input, expected_output in test_dates:
            result = self.ingestor._parse_date(date_input)
            assert result == expected_output

    def test_offset_progression_no_gaps(self):
        """Test that offset progression has no gaps during continuous ingestion"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100, 197)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(197, 285)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(285, 385)]},
            {'packages': []},
        ]

        expected_offsets = [0, 100, 197, 285]
        actual_offsets = []

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            offset = 0
            for items_batch in self.ingestor.paginate_api_response(config, offset):
                actual_offsets.append(offset)
                offset += len(items_batch)

            assert actual_offsets == expected_offsets
            assert offset == 385

    def test_batch_insertion_consistency(self):
        """Test that batch insertion maintains data consistency"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        test_items = [
            {'packageId': 'BILLS-118hr1-2023-01-01', 'dateIssued': '2023-01-01'},
            {'packageId': 'BILLS-118hr2-2023-01-02', 'dateIssued': '2023-01-02'},
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            result = self.ingestor.insert_batch(config, test_items)

            assert result == 2

            cursor.execute.assert_called_once()
            query = cursor.execute.call_args[0][0]
            assert 'ON CONFLICT' in query


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
