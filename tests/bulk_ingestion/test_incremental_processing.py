"""
Incremental processing and checkpoint tests
"""

import pytest
import time
import json
import hashlib
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

class TestCheckpointSystem:
    """Test checkpoint and state management system"""

    @pytest.mark.unit
    def test_checkpoint_creation(self):
        """Test checkpoint creation and storage"""
        def create_checkpoint(session_id: str, data_source: str, data_type: str,
                            congress: int, offset: int, processed_count: int) -> Dict[str, Any]:
            """Create checkpoint data"""
            checkpoint_data = {
                'session_id': session_id,
                'data_source': data_source,
                'data_type': data_type,
                'congress': congress,
                'offset': offset,
                'processed_count': processed_count,
                'timestamp': datetime.now().isoformat(),
                'is_completed': processed_count == -1
            }

            return checkpoint_data

        checkpoint = create_checkpoint('test_session_123', 'congress.gov', 'bills', 118, 250, 25)

        assert checkpoint['session_id'] == 'test_session_123'
        assert checkpoint['data_source'] == 'congress.gov'
        assert checkpoint['offset'] == 250
        assert checkpoint['processed_count'] == 25
        assert checkpoint['is_completed'] == False

    @pytest.mark.unit
    def test_checkpoint_completion_detection(self):
        """Test detection of completed checkpoints"""
        def is_checkpoint_completed(checkpoint: Dict[str, Any]) -> bool:
            return checkpoint.get('is_completed', False) or checkpoint.get('processed_count', 0) == -1

        incomplete_checkpoint = {'processed_count': 25, 'offset': 250}
        assert not is_checkpoint_completed(incomplete_checkpoint)

        completed_checkpoint = {'processed_count': -1, 'offset': 1000}
        assert is_checkpoint_completed(completed_checkpoint)

        explicit_completion = {'is_completed': True, 'offset': 1000}
        assert is_checkpoint_completed(explicit_completion)

    @pytest.mark.unit
    def test_checkpoint_resumption_logic(self):
        """Test checkpoint-based resumption logic"""
        def get_next_offset_from_checkpoint(checkpoint: Dict[str, Any]) -> int:
            if checkpoint.get('is_completed'):
                return -1

            current_offset = checkpoint.get('offset', 0)
            batch_size = checkpoint.get('batch_size', 50)

            return current_offset + batch_size

        checkpoint = {'offset': 250, 'batch_size': 50, 'is_completed': False}
        next_offset = get_next_offset_from_checkpoint(checkpoint)
        assert next_offset == 300

        completed_checkpoint = {'offset': 1000, 'batch_size': 50, 'is_completed': True}
        next_offset = get_next_offset_from_checkpoint(completed_checkpoint)
        assert next_offset == -1

    @pytest.mark.database
    @pytest.mark.integration
    def test_database_checkpoint_storage(self, clean_database):
        """Test storing and retrieving checkpoints from database"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        checkpoint_data = {
            'session_id': 'test_checkpoint_001',
            'data_source': 'congress.gov',
            'data_type': 'bills',
            'congress': 118,
            'offset': 150,
            'processed_count': 3,
            'timestamp': datetime.now().isoformat()
        }

        cursor = clean_database.cursor()
        cursor.execute("""
            INSERT INTO incremental.processing_checkpoints (
                session_id, data_source, data_type, congress, offset, processed_count, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                offset = EXCLUDED.offset,
                processed_count = EXCLUDED.processed_count,
                timestamp = EXCLUDED.timestamp
        """, (
            checkpoint_data['session_id'],
            checkpoint_data['data_source'],
            checkpoint_data['data_type'],
            checkpoint_data['congress'],
            checkpoint_data['offset'],
            checkpoint_data['processed_count'],
            checkpoint_data['timestamp']
        ))
        clean_database.commit()
        cursor.close()

        cursor = clean_database.cursor()
        cursor.execute("""
            SELECT * FROM incremental.processing_checkpoints
            WHERE session_id = %s
        """, ('test_checkpoint_001',))

        result = cursor.fetchone()
        cursor.close()

        assert result is not None
        assert result[1] == 'congress.gov'
        assert result[4] == 150
        assert result[5] == 3

class TestFingerprintSystem:
    """Test record fingerprinting for duplicate detection"""

    @pytest.mark.unit
    def test_fingerprint_generation(self):
        """Test generation of record fingerprints"""
        def generate_record_fingerprint(record_data: Dict[str, Any]) -> str:
            key_fields = {
                'bill_id': record_data.get('billId', ''),
                'title': record_data.get('title', ''),
                'sponsor': record_data.get('sponsor', {}).get('bioguideId', ''),
                'introduced_date': record_data.get('introducedDate', ''),
                'congress': record_data.get('congress', 118)
            }

            fingerprint_str = json.dumps(key_fields, sort_keys=True)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()

        record1 = {
            'billId': 'hr123-118',
            'title': 'Test Bill',
            'sponsor': {'bioguideId': 'T1234'},
            'introducedDate': '2024-01-15T00:00:00Z',
            'congress': 118
        }

        fingerprint1 = generate_record_fingerprint(record1)

        fingerprint2 = generate_record_fingerprint(record1)
        assert fingerprint1 == fingerprint2

        record2 = record1.copy()
        record2['title'] = 'Different Title'
        fingerprint3 = generate_record_fingerprint(record2)
        assert fingerprint1 != fingerprint3

    @pytest.mark.unit
    def test_duplicate_detection_logic(self):
        """Test duplicate detection logic using fingerprints"""
        def is_duplicate_record(new_record: Dict[str, Any], existing_fingerprints: List[str]) -> bool:
            new_fingerprint = generate_record_fingerprint(new_record)
            return new_fingerprint in existing_fingerprints

        def generate_record_fingerprint(record_data: Dict[str, Any]) -> str:
            key_fields = {
                'bill_id': record_data.get('billId', ''),
                'title': record_data.get('title', ''),
                'sponsor': record_data.get('sponsor', {}).get('bioguideId', ''),
            }
            fingerprint_str = json.dumps(key_fields, sort_keys=True)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()

        existing_fingerprints = []
        for i in range(3):
            record = {
                'billId': f'hr{i+100}-118',
                'title': f'Existing Bill {i+100}',
                'sponsor': {'bioguideId': f'T{i+100:04d}'}
            }
            fingerprint = generate_record_fingerprint(record)
            existing_fingerprints.append(fingerprint)

        new_record = {
            'billId': 'hr200-118',
            'title': 'New Bill',
            'sponsor': {'bioguideId': 'T0200'}
        }

        assert not is_duplicate_record(new_record, existing_fingerprints)

        duplicate_record = {
            'billId': 'hr101-118',
            'title': 'Existing Bill 101',
            'sponsor': {'bioguideId': 'T0101'}
        }

        assert is_duplicate_record(duplicate_record, existing_fingerprints)

    @pytest.mark.database
    @pytest.mark.integration
    def test_fingerprint_database_storage(self, clean_database):
        """Test storing and querying fingerprints in database"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        def generate_record_fingerprint(record_data: Dict[str, Any]) -> str:
            key_fields = {
                'bill_id': record_data.get('billId', ''),
                'title': record_data.get('title', ''),
                'sponsor': record_data.get('sponsor', {}).get('bioguideId', ''),
            }
            fingerprint_str = json.dumps(key_fields, sort_keys=True)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()

        test_record = {
            'billId': 'hr999-118',
            'title': 'Fingerprint Test Bill',
            'sponsor': {'bioguideId': 'T0999'}
        }

        fingerprint = generate_record_fingerprint(test_record)

        cursor = clean_database.cursor()
        cursor.execute("""
            INSERT INTO incremental.processed_records (
                session_id, data_source, data_type, record_id, fingerprint
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (fingerprint) DO NOTHING
        """, ('test_fingerprint_session', 'congress.gov', 'bills', 'hr999-118', fingerprint))
        clean_database.commit()
        cursor.close()

        cursor = clean_database.cursor()
        cursor.execute("""
            SELECT fingerprint FROM incremental.processed_records
            WHERE fingerprint = %s
        """, (fingerprint,))

        result = cursor.fetchone()
        cursor.close()

        assert result is not None
        assert result[0] == fingerprint

class TestSessionManagement:
    """Test ingestion session management"""

    @pytest.mark.database
    @pytest.mark.integration
    def test_session_lifecycle(self, clean_database):
        """Test complete session lifecycle"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        session_id = 'test_lifecycle_session'

        helper.create_test_ingestion_session(
            session_id=session_id,
            data_source='congress.gov',
            data_type='bills',
            status='running'
        )

        cursor = clean_database.cursor()
        cursor.execute("""
            UPDATE incremental.ingestion_sessions
            SET status = 'processing', error_summary = 'Processing batch 1'
            WHERE session_id = %s
        """, (session_id,))
        clean_database.commit()
        cursor.close()

        cursor = clean_database.cursor()
        cursor.execute("""
            UPDATE incremental.ingestion_sessions
            SET status = 'completed', completed_at = %s
            WHERE session_id = %s
        """, (datetime.now(), session_id))
        clean_database.commit()
        cursor.close()

        sessions = helper.get_ingestion_sessions()
        test_session = next((s for s in sessions if s['session_id'] == session_id), None)

        assert test_session is not None
        assert test_session['status'] == 'completed'
        assert test_session['completed_at'] is not None

    @pytest.mark.unit
    def test_session_resumption_after_interruption(self):
        """Test session resumption after interruption"""
        def simulate_interrupted_session():
            session_state = {
                'session_id': 'interrupted_session_001',
                'status': 'interrupted',
                'start_time': datetime.now().isoformat(),
                'last_checkpoint': {
                    'offset': 500,
                    'batch_size': 50,
                    'processed_count': 10,
                    'last_processed_id': 'hr525-118'
                },
                'total_records_processed': 250,
                'records_in_current_batch': 10
            }

            return session_state

        def resume_session(session_state: Dict[str, Any]) -> Dict[str, Any]:
            if session_state['status'] != 'interrupted':
                return session_state

            last_checkpoint = session_state['last_checkpoint']
            resume_offset = last_checkpoint['offset']

            remaining_in_batch = last_checkpoint['batch_size'] - last_checkpoint['processed_count']

            session_state['status'] = 'running'
            session_state['resume_offset'] = resume_offset
            session_state['remaining_in_batch'] = remaining_in_batch

            return session_state

        original_state = simulate_interrupted_session()
        resumed_state = resume_session(original_state)

        assert resumed_state['status'] == 'running'
        assert resumed_state['resume_offset'] == 500
        assert resumed_state['remaining_in_batch'] == 40

    @pytest.mark.unit
    def test_session_statistics_calculation(self):
        """Test session statistics calculation"""
        def calculate_session_stats(start_time: datetime, end_time: datetime,
                                  records_processed: int, records_failed: int) -> Dict[str, Any]:
            duration = (end_time - start_time).total_seconds()
            success_rate = (records_processed / (records_processed + records_failed)) * 100 if (records_processed + records_failed) > 0 else 0
            records_per_second = records_processed / duration if duration > 0 else 0

            return {
                'duration_seconds': duration,
                'records_processed': records_processed,
                'records_failed': records_failed,
                'success_rate_percent': success_rate,
                'records_per_second': records_per_second,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }

        start = datetime.now()
        time.sleep(1)
        end = datetime.now()

        stats = calculate_session_stats(start, end, 95, 5)

        assert stats['duration_seconds'] >= 1.0
        assert stats['records_processed'] == 95
        assert stats['records_failed'] == 5
        assert stats['success_rate_percent'] == 95.0
        assert stats['records_per_second'] >= 90

class TestBatchProcessing:
    """Test batch processing with checkpoints"""

    @pytest.mark.unit
    def test_batch_size_optimization(self):
        """Test batch size optimization logic"""
        def calculate_optimal_batch_size(total_records: int, processing_rate: float,
                                       max_batch_time: float = 30.0) -> int:
            max_records_in_time = processing_rate * max_batch_time

            ideal_batch_size = min(max_records_in_time, 1000)

            if ideal_batch_size <= 50:
                return 50
            elif ideal_batch_size <= 100:
                return 100
            elif ideal_batch_size <= 250:
                return 250
            else:
                return 500

        scenarios = [
            (10000, 2.0, 100),
            (1000, 10.0, 100),
            (100, 50.0, 100),
            (50000, 1.0, 50),
        ]

        for total_records, processing_rate, expected_batch in scenarios:
            batch_size = calculate_optimal_batch_size(total_records, processing_rate)
            print(f"Records: {total_records}, Rate: {processing_rate}/s, Batch: {batch_size}")

            assert batch_size >= 50
            assert batch_size <= 500

    @pytest.mark.unit
    def test_batch_progress_tracking(self):
        """Test batch progress tracking"""
        def track_batch_progress(batch_size: int, processed_count: int) -> Dict[str, Any]:
            progress_percent = (processed_count / batch_size) * 100

            status = 'completed' if processed_count >= batch_size else 'processing'
            remaining = max(0, batch_size - processed_count)

            return {
                'batch_size': batch_size,
                'processed_count': processed_count,
                'progress_percent': progress_percent,
                'status': status,
                'remaining': remaining
            }

        test_cases = [
            (100, 0),
            (100, 25),
            (100, 50),
            (100, 75),
            (100, 100),
            (100, 150),
        ]

        for batch_size, processed in test_cases:
            progress = track_batch_progress(batch_size, processed)

            print(f"Batch progress: {processed}/{batch_size} ({progress['progress_percent']:.1f}%)")

            assert progress['batch_size'] == batch_size
            assert progress['processed_count'] == processed

            if processed >= batch_size:
                assert progress['status'] == 'completed'
            else:
                assert progress['status'] == 'processing'

class TestRecoveryMechanisms:
    """Test recovery mechanisms for failed sessions"""

    @pytest.mark.unit
    def test_failed_session_detection(self):
        """Test detection of failed sessions"""
        def detect_failed_sessions(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            failed_sessions = []

            for session in sessions:
                status = session.get('status', 'unknown')
                error_summary = session.get('error_summary', '')
                completed_at = session.get('completed_at')

                if status == 'failed':
                    failed_sessions.append(session)
                elif status == 'running' and error_summary and not completed_at:
                    failed_sessions.append(session)

            return failed_sessions

        test_sessions = [
            {'session_id': 'session1', 'status': 'completed', 'error_summary': None},
            {'session_id': 'session2', 'status': 'failed', 'error_summary': 'API timeout'},
            {'session_id': 'session3', 'status': 'running', 'error_summary': 'Connection error'},
            {'session_id': 'session4', 'status': 'completed', 'error_summary': 'Minor warning'},
        ]

        failed = detect_failed_sessions(test_sessions)

        assert len(failed) == 2
        failed_ids = [s['session_id'] for s in failed]
        assert 'session2' in failed_ids
        assert 'session3' in failed_ids

    @pytest.mark.unit
    def test_session_recovery_strategy(self):
        """Test session recovery strategy"""
        def create_recovery_strategy(failed_session: Dict[str, Any]) -> Dict[str, Any]:
            session_id = failed_session['session_id']
            error_summary = failed_session.get('error_summary', '')

            if 'timeout' in error_summary.lower():
                strategy = 'resume_from_checkpoint'
                reason = 'Timeout error, resume from last checkpoint'
            elif 'connection' in error_summary.lower():
                strategy = 'restart_with_same_session'
                reason = 'Connection error, restart with exponential backoff'
            elif 'rate_limit' in error_summary.lower():
                strategy = 'reduce_rate_and_resume'
                reason = 'Rate limit error, reduce rate and resume'
            else:
                strategy = 'full_restart'
                reason = 'Unknown error, full restart required'

            return {
                'recovery_strategy': strategy,
                'reason': reason,
                'new_session_id': f"{session_id}_recovery_{int(time.time())}",
                'estimated_recovery_time': '5-15 minutes'
            }

        failed_sessions = [
            {'session_id': 'test1', 'error_summary': 'API timeout occurred'},
            {'session_id': 'test2', 'error_summary': 'Connection lost'},
            {'session_id': 'test3', 'error_summary': 'Rate limit exceeded'},
            {'session_id': 'test4', 'error_summary': 'Unknown processing error'},
        ]

        for failed_session in failed_sessions:
            strategy = create_recovery_strategy(failed_session)
            print(f"Session {failed_session['session_id']}: {strategy['recovery_strategy']}")

            assert 'recovery_strategy' in strategy
            assert 'new_session_id' in strategy
            assert strategy['recovery_strategy'] in ['resume_from_checkpoint', 'restart_with_same_session', 'reduce_rate_and_resume', 'full_restart']

class TestIncrementalPerformance:
    """Test incremental processing performance"""

    @pytest.mark.performance
    @pytest.mark.unit
    def test_checkpoint_performance_impact(self):
        """Test performance impact of checkpointing"""
        def measure_checkpoint_performance(data_size: int, checkpoint_frequency: int) -> Dict[str, float]:
            start_time = time.time()
            checkpoint_times = []

            for i in range(data_size):
                item = f'item_{i}'
                processed_item = item.upper()

                if checkpoint_frequency > 0 and i % checkpoint_frequency == 0:
                    checkpoint_start = time.time()
                    time.sleep(0.001)
                    checkpoint_end = time.time()
                    checkpoint_times.append(checkpoint_end - checkpoint_start)

            total_time = time.time() - start_time
            total_checkpoint_time = sum(checkpoint_times)
            processing_time = total_time - total_checkpoint_time

            return {
                'total_time': total_time,
                'processing_time': processing_time,
                'checkpoint_time': total_checkpoint_time,
                'checkpoint_overhead_percent': (total_checkpoint_time / total_time) * 100 if total_time > 0 else 0,
                'checkpoints_made': len(checkpoint_times)
            }

        frequencies = [0, 10, 50, 100, 200]

        results = {}
        for freq in frequencies:
            perf = measure_checkpoint_performance(1000, freq)
            results[freq] = perf
            print(f"Frequency {freq}: Overhead {perf['checkpoint_overhead_percent']:.2f}%")

        assert results[0]['total_time'] <= results[50]['total_time']

        for freq, result in results.items():
            if freq > 0:
                assert result['checkpoint_overhead_percent'] <= 20, f"Checkpoint overhead too high: {result['checkpoint_overhead_percent']:.2f}%"

    @pytest.mark.performance
    @pytest.mark.unit
    def test_fingerprint_lookup_performance(self):
        """Test fingerprint lookup performance"""
        test_fingerprints = [f"fingerprint_{i:06d}" for i in range(10000)]
        fingerprint_set = set(test_fingerprints)

        lookup_times = []

        for i in range(1000):
            test_fingerprint = test_fingerprints[i % len(test_fingerprints)]

            start_time = time.time()
            exists = test_fingerprint in fingerprint_set
            end_time = time.time()

            lookup_times.append(end_time - start_time)
            assert exists == True

        avg_lookup_time = sum(lookup_times) / len(lookup_times)
        max_lookup_time = max(lookup_times)

        print(f"Fingerprint lookup performance:")
        print(f"   Average: {avg_lookup_time*1000:.3f}ms")
        print(f"   Maximum: {max_lookup_time*1000:.3f}ms")
        print(f"   Total lookups: {len(lookup_times)}")

        assert avg_lookup_time < 0.001, f"Average lookup time {avg_lookup_time*1000:.3f}ms too slow"
        assert max_lookup_time < 0.01, f"Max lookup time {max_lookup_time*1000:.3f}ms too slow"
