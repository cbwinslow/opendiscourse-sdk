#!/usr/bin/env python3
"""
Sub-Agent Manager

This script manages individual sub-agents, providing them with
specific tasks, monitoring their progress, and handling communication.
"""

import asyncio
import json
import os
import queue
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import websockets

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

class MessageType(Enum):
    """Message types for agent communication"""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_UPDATE = "task_update"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    HEARTBEAT = "heartbeat"
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"
    SHUTDOWN = "shutdown"

class AgentState(Enum):
    """Agent operational states"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class AgentMessage:
    """Message between orchestrator and agents"""
    message_id: str
    message_type: MessageType
    sender_id: str
    recipient_id: str
    timestamp: datetime
    payload: Dict[str, Any]

@dataclass
class AgentTask:
    """Task definition for sub-agent"""
    task_id: str
    task_type: str
    phase_number: int
    script_path: str
    arguments: List[str]
    requirements: Dict[str, Any]
    priority: int
    timeout_seconds: int

@dataclass
class AgentInfo:
    """Information about a sub-agent"""
    agent_id: str
    agent_type: str
    state: AgentState
    current_task: Optional[AgentTask]
    last_heartbeat: datetime
    total_tasks_completed: int
    total_tasks_failed: int
    capabilities: List[str]

class SubAgentManager:
    """Manages sub-agents and their communication"""

    def __init__(self):
        self.manager_start = datetime.now()
        self.agents: Dict[str, AgentInfo] = {}
        self.message_queue = queue.Queue()
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.running = False
        self.heartbeat_interval = 30  # seconds
        self.agent_timeout = 120  # seconds

        # Register message handlers
        self._register_message_handlers()

        # Start background threads
        self._start_background_threads()

    def _register_message_handlers(self):
        """Register message type handlers"""
        self.message_handlers[MessageType.TASK_UPDATE] = self._handle_task_update
        self.message_handlers[MessageType.TASK_COMPLETE] = self._handle_task_complete
        self.message_handlers[MessageType.TASK_ERROR] = self._handle_task_error
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.STATUS_RESPONSE] = self._handle_status_response

    def _start_background_threads(self):
        """Start background processing threads"""
        self.running = True

        # Message processing thread
        self.message_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.message_thread.start()

        # Heartbeat monitoring thread
        self.heartbeat_thread = threading.Thread(target=self._monitor_heartbeats, daemon=True)
        self.heartbeat_thread.start()

    def register_agent(self, agent_info: AgentInfo):
        """Register a new sub-agent"""
        self.agents[agent_info.agent_id] = agent_info
        print(f"📝 Registered agent: {agent_info.agent_id} ({agent_info.agent_type})")

        # Send welcome message
        welcome_msg = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.STATUS_REQUEST,
            sender_id="manager",
            recipient_id=agent_info.agent_id,
            timestamp=datetime.now(),
            payload={"action": "welcome"}
        )

        self.message_queue.put(welcome_msg)

    def unregister_agent(self, agent_id: str):
        """Unregister a sub-agent"""
        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            print(f"🗑️  Unregistered agent: {agent_id} ({agent_info.agent_type})")
            del self.agents[agent_id]

    def assign_task(self, agent_id: str, task: AgentTask) -> bool:
        """Assign a task to a specific agent"""
        if agent_id not in self.agents:
            print(f"❌ Agent {agent_id} not found")
            return False

        agent_info = self.agents[agent_id]
        if agent_info.state != AgentState.IDLE:
            print(f"❌ Agent {agent_id} is not idle (state: {agent_info.state})")
            return False

        # Update agent state
        agent_info.state = AgentState.BUSY
        agent_info.current_task = task

        # Send task assignment message
        task_msg = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id="manager",
            recipient_id=agent_id,
            timestamp=datetime.now(),
            payload={"task": asdict(task)}
        )

        self.message_queue.put(task_msg)
        print(f"📋 Assigned task {task.task_id} to agent {agent_id}")

        return True

    def get_available_agents(self, capability: str = None) -> List[str]:
        """Get list of available agents"""
        available = []

        for agent_id, agent_info in self.agents.items():
            if agent_info.state == AgentState.IDLE:
                if capability is None or capability in agent_info.capabilities:
                    available.append(agent_id)

        return available

    def get_agent_status(self, agent_id: str) -> Optional[AgentInfo]:
        """Get status of a specific agent"""
        return self.agents.get(agent_id)

    def get_all_agents_status(self) -> Dict[str, AgentInfo]:
        """Get status of all agents"""
        return self.agents.copy()

    def send_message(self, message: AgentMessage):
        """Send a message to an agent"""
        self.message_queue.put(message)

    def _process_messages(self):
        """Process messages in the queue"""
        while self.running:
            try:
                # Get message from queue
                message = self.message_queue.get(timeout=1)

                # Route to appropriate handler
                message_type = message.message_type
                if message_type in self.message_handlers:
                    handler = self.message_handlers[message_type]
                    handler(message)
                else:
                    print(f"⚠️  No handler for message type: {message_type}")

                self.message_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error processing message: {e}")

    def _handle_task_update(self, message: AgentMessage):
        """Handle task update message"""
        agent_id = message.sender_id
        payload = message.payload

        if agent_id in self.agents:
            agent_info = self.agents[agent_id]

            # Update agent's last heartbeat
            agent_info.last_heartbeat = message.timestamp

            print(f"📊 Agent {agent_id} task update: {payload.get('status', 'unknown')}")

    def _handle_task_complete(self, message: AgentMessage):
        """Handle task completion message"""
        agent_id = message.sender_id
        payload = message.payload

        if agent_id in self.agents:
            agent_info = self.agents[agent_id]

            # Update agent state
            agent_info.state = AgentState.IDLE
            agent_info.current_task = None
            agent_info.total_tasks_completed += 1
            agent_info.last_heartbeat = message.timestamp

            print(f"✅ Agent {agent_id} completed task: {payload.get('task_id', 'unknown')}")

    def _handle_task_error(self, message: AgentMessage):
        """Handle task error message"""
        agent_id = message.sender_id
        payload = message.payload

        if agent_id in self.agents:
            agent_info = self.agents[agent_id]

            # Update agent state
            agent_info.state = AgentState.IDLE
            agent_info.current_task = None
            agent_info.total_tasks_failed += 1
            agent_info.last_heartbeat = message.timestamp

            print(f"❌ Agent {agent_id} task error: {payload.get('error', 'unknown')}")

    def _handle_heartbeat(self, message: AgentMessage):
        """Handle heartbeat message"""
        agent_id = message.sender_id

        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            agent_info.last_heartbeat = message.timestamp

            # Update agent state if needed
            payload = message.payload
            reported_state = payload.get('state', 'idle')

            if reported_state == 'idle' and agent_info.state == AgentState.BUSY:
                # Agent might have completed a task without sending completion message
                agent_info.state = AgentState.IDLE
                agent_info.current_task = None
            elif reported_state == 'busy':
                agent_info.state = AgentState.BUSY
            elif reported_state == 'error':
                agent_info.state = AgentState.ERROR

    def _handle_status_response(self, message: AgentMessage):
        """Handle status response message"""
        agent_id = message.sender_id
        payload = message.payload

        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            agent_info.last_heartbeat = message.timestamp

            # Update agent info from payload
            if 'capabilities' in payload:
                agent_info.capabilities = payload['capabilities']
            if 'state' in payload:
                agent_info.state = AgentState(payload['state'])

    def _monitor_heartbeats(self):
        """Monitor agent heartbeats and detect timeouts"""
        while self.running:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(seconds=self.agent_timeout)

                for agent_id, agent_info in list(self.agents.items()):
                    if agent_info.last_heartbeat < timeout_threshold:
                        print(f"⚠️  Agent {agent_id} heartbeat timeout")
                        agent_info.state = AgentState.OFFLINE

                # Send heartbeat requests to offline agents
                for agent_id, agent_info in self.agents.items():
                    if agent_info.state == AgentState.OFFLINE:
                        heartbeat_msg = AgentMessage(
                            message_id=str(uuid.uuid4()),
                            message_type=MessageType.HEARTBEAT,
                            sender_id="manager",
                            recipient_id=agent_id,
                            timestamp=current_time,
                            payload={"action": "ping"}
                        )
                        self.message_queue.put(heartbeat_msg)

                time.sleep(self.heartbeat_interval)

            except Exception as e:
                print(f"❌ Error in heartbeat monitoring: {e}")

    def shutdown(self):
        """Shutdown the sub-agent manager"""
        print("🛑 Shutting down sub-agent manager...")

        # Send shutdown messages to all agents
        shutdown_msg = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.SHUTDOWN,
            sender_id="manager",
            recipient_id="broadcast",
            timestamp=datetime.now(),
            payload={"action": "shutdown"}
        )

        self.message_queue.put(shutdown_msg)

        # Stop background threads
        self.running = False

        # Wait for threads to finish
        if hasattr(self, 'message_thread'):
            self.message_thread.join(timeout=5)
        if hasattr(self, 'heartbeat_thread'):
            self.heartbeat_thread.join(timeout=5)

        print("✅ Sub-agent manager shutdown complete")

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics"""
        total_agents = len(self.agents)
        idle_agents = sum(1 for a in self.agents.values() if a.state == AgentState.IDLE)
        busy_agents = sum(1 for a in self.agents.values() if a.state == AgentState.BUSY)
        error_agents = sum(1 for a in self.agents.values() if a.state == AgentState.ERROR)
        offline_agents = sum(1 for a in self.agents.values() if a.state == AgentState.OFFLINE)

        total_completed = sum(a.total_tasks_completed for a in self.agents.values())
        total_failed = sum(a.total_tasks_failed for a in self.agents.values())

        return {
            'manager_start_time': self.manager_start.isoformat(),
            'total_agents': total_agents,
            'idle_agents': idle_agents,
            'busy_agents': busy_agents,
            'error_agents': error_agents,
            'offline_agents': offline_agents,
            'total_tasks_completed': total_completed,
            'total_tasks_failed': total_failed,
            'success_rate': (total_completed / (total_completed + total_failed) * 100) if (total_completed + total_failed) > 0 else 0
        }

class SubAgent:
    """Base class for sub-agents"""

    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.state = AgentState.IDLE
        self.current_task = None
        self.manager_url = None
        self.websocket = None
        self.running = False

        # Agent statistics
        self.start_time = datetime.now()
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.last_heartbeat = datetime.now()

    async def connect_to_manager(self, manager_url: str):
        """Connect to the sub-agent manager"""
        self.manager_url = manager_url

        try:
            self.websocket = await websockets.connect(manager_url)
            self.running = True

            print(f"🔗 Connected to manager: {manager_url}")

            # Start message handling
            asyncio.create_task(self._handle_messages())
            asyncio.create_task(self._send_heartbeats())

        except Exception as e:
            print(f"❌ Failed to connect to manager: {e}")
            raise

    async def _handle_messages(self):
        """Handle messages from manager"""
        while self.running and self.websocket:
            try:
                message_str = await self.websocket.recv()
                message_data = json.loads(message_str)

                # Convert to AgentMessage
                message = AgentMessage(
                    message_id=message_data['message_id'],
                    message_type=MessageType(message_data['message_type']),
                    sender_id=message_data['sender_id'],
                    recipient_id=message_data['recipient_id'],
                    timestamp=datetime.fromisoformat(message_data['timestamp']),
                    payload=message_data['payload']
                )

                await self._process_message(message)

            except websockets.exceptions.ConnectionClosed:
                print("🔌 Connection to manager closed")
                break
            except Exception as e:
                print(f"❌ Error handling message: {e}")
                break

    async def _process_message(self, message: AgentMessage):
        """Process incoming message"""
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            await self._handle_task_assignment(message)
        elif message.message_type == MessageType.STATUS_REQUEST:
            await self._handle_status_request(message)
        elif message.message_type == MessageType.SHUTDOWN:
            await self._handle_shutdown(message)
        else:
            print(f"⚠️  Unknown message type: {message.message_type}")

    async def _handle_task_assignment(self, message: AgentMessage):
        """Handle task assignment"""
        task_data = message.payload['task']
        task = AgentTask(**task_data)

        print(f"📋 Received task assignment: {task.task_id}")

        self.current_task = task
        self.state = AgentState.BUSY

        # Execute task
        try:
            await self._execute_task(task)

            # Send completion message
            await self._send_message(MessageType.TASK_COMPLETE, {
                'task_id': task.task_id,
                'result': 'success'
            })

            self.tasks_completed += 1
            self.state = AgentState.IDLE
            self.current_task = None

        except Exception as e:
            print(f"❌ Task execution failed: {e}")

            # Send error message
            await self._send_message(MessageType.TASK_ERROR, {
                'task_id': task.task_id,
                'error': str(e)
            })

            self.tasks_failed += 1
            self.state = AgentState.ERROR
            self.current_task = None

    async def _execute_task(self, task: AgentTask):
        """Execute a task (to be implemented by subclasses)"""
        # This should be implemented by specific agent types
        raise NotImplementedError("Task execution must be implemented by subclass")

    async def _handle_status_request(self, message: AgentMessage):
        """Handle status request"""
        await self._send_message(MessageType.STATUS_RESPONSE, {
            'state': self.state.value,
            'capabilities': self.capabilities,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed
        })

    async def _handle_shutdown(self, message: AgentMessage):
        """Handle shutdown message"""
        print("🛑 Received shutdown message")
        self.running = False
        if self.websocket:
            await self.websocket.close()

    async def _send_message(self, message_type: MessageType, payload: Dict[str, Any]):
        """Send a message to the manager"""
        if not self.websocket:
            return

        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_id=self.agent_id,
            recipient_id="manager",
            timestamp=datetime.now(),
            payload=payload
        )

        message_data = {
            'message_id': message.message_id,
            'message_type': message.message_type.value,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id,
            'timestamp': message.timestamp.isoformat(),
            'payload': message.payload
        }

        try:
            await self.websocket.send(json.dumps(message_data))
        except Exception as e:
            print(f"❌ Failed to send message: {e}")

    async def _send_heartbeats(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                await self._send_message(MessageType.HEARTBEAT, {
                    'state': self.state.value,
                    'timestamp': datetime.now().isoformat()
                })

                self.last_heartbeat = datetime.now()
                await asyncio.sleep(30)  # 30 second intervals

            except Exception as e:
                print(f"❌ Failed to send heartbeat: {e}")
                break

    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'state': self.state.value,
            'start_time': self.start_time.isoformat(),
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'capabilities': self.capabilities
        }

def main():
    """Main function for sub-agent manager"""
    import argparse

    parser = argparse.ArgumentParser(description='Sub-Agent Manager')
    parser.add_argument('--mode', choices=['manager', 'agent'],
                       default='manager', help='Run as manager or agent')
    parser.add_argument('--agent-id', help='Agent ID (agent mode only)')
    parser.add_argument('--agent-type', help='Agent type (agent mode only)')
    parser.add_argument('--capabilities', nargs='+', help='Agent capabilities (agent mode only)')

    args = parser.parse_args()

    if args.mode == 'manager':
        # Run as manager
        manager = SubAgentManager()

        try:
            # Example usage
            print("🚀 Sub-Agent Manager started")
            print("Press Ctrl+C to shutdown...")

            # Keep running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested")
            manager.shutdown()

    elif args.mode == 'agent':
        # Run as agent
        if not args.agent_id or not args.agent_type:
            print("❌ Agent mode requires --agent-id and --agent-type")
            sys.exit(1)

        capabilities = args.capabilities or []
        agent = SubAgent(args.agent_id, args.agent_type, capabilities)

        try:
            print(f"🤖 Agent {args.agent_id} ({args.agent_type}) started")
            print("Press Ctrl+C to shutdown...")

            # Keep running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested")
            agent.running = False

if __name__ == "__main__":
    main()
