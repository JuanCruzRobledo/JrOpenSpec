---
sprint: 7
artifact: design
status: complete
---

# SDD Design — Sprint 7: WebSocket Gateway + Carrito Compartido

## Status: APPROVED

---

## 1. Service Topology

```
                    ┌─────────────┐
                    │   NGINX /   │
                    │  API Gateway│
                    │  (future)   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
    ┌─────────▼─────────┐   ┌──────────▼──────────┐
    │   REST API (:8000) │   │  WS Gateway (:8001)  │
    │   FastAPI          │   │  FastAPI WebSocket    │
    │                    │   │                       │
    │  /api/auth/*       │   │  /ws/waiter?token=JWT │
    │  /api/sessions/*/  │   │  /ws/kitchen?token=JWT│
    │    cart/items       │   │  /ws/admin?token=JWT  │
    │  /api/menu/*       │   │  /ws/diner?table_token│
    │  /api/health/*     │   │  /health              │
    └────────┬───────────┘   └──────────┬────────────┘
             │                          │
             │    ┌─────────────┐       │
             ├───►│  PostgreSQL  │◄──────┤
             │    │  :5432       │       │
             │    └─────────────┘       │
             │                          │
             │    ┌─────────────┐       │
             └───►│  Redis 7     │◄──────┘
                  │  :6379       │
                  │  DB 0: cache │
                  │  DB 1: auth  │
                  │  Pub/Sub     │
                  └─────────────┘
```

### Docker Compose Addition

```yaml
# Add to existing docker-compose.yml
gateway:
  build:
    context: .
    dockerfile: ws_gateway/Dockerfile
  ports:
    - "8001:8001"
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    - TABLE_TOKEN_SECRET_KEY=${TABLE_TOKEN_SECRET_KEY}
    - WS_MAX_CONNECTIONS=1000
    - WS_MAX_PER_USER=3
    - WS_HEARTBEAT_INTERVAL=30
    - WS_HEARTBEAT_TIMEOUT=60
    - WS_CLEANUP_INTERVAL=30
    - WS_ORIGIN_WHITELIST=http://localhost:5173,http://localhost:5174
    - WS_STAFF_REAUTH_SECONDS=300
    - WS_DINER_REAUTH_SECONDS=1800
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  volumes:
    - ./shared:/app/shared
  networks:
    - buen-sabor-net
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
    interval: 10s
    start_period: 10s
    retries: 3
```

---

## 2. Connection Manager Class Design

```python
# ws_gateway/core/connection_manager.py

from dataclasses import dataclass, field
from datetime import datetime
from asyncio import Lock, wait_for, TimeoutError
from collections import defaultdict
from fastapi import WebSocket
import logging

logger = logging.getLogger("ws_gateway.connection_manager")

@dataclass
class ConnectionMetadata:
    """Immutable metadata attached to each WebSocket connection."""
    user_id: int | None          # None for diners (they use diner_id)
    diner_id: str | None         # None for staff
    tenant_id: int
    branch_id: int
    role: str                    # "waiter", "kitchen", "admin", "diner"
    session_id: str | None       # Only for diners
    table_id: int | None         # Only for diners
    sector_id: int | None        # Only for waiters with assigned sector
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    last_reauth: datetime = field(default_factory=datetime.utcnow)
    auth_strategy: str = ""      # "staff_jwt" or "diner_table_token"

    @property
    def identity_key(self) -> str:
        """Unique identity for connection limit tracking."""
        if self.user_id is not None:
            return f"user:{self.user_id}"
        return f"diner:{self.diner_id}"


class ShardedLocks:
    """Lock manager with automatic creation and acquisition timeout."""

    def __init__(self, timeout: float = 5.0):
        self._timeout = timeout
        self._global = Lock()
        self._user: dict[str, Lock] = defaultdict(Lock)
        self._branch: dict[int, Lock] = defaultdict(Lock)
        self._sector: dict[int, Lock] = defaultdict(Lock)
        self._session: dict[str, Lock] = defaultdict(Lock)

    async def acquire_global(self):
        return await wait_for(self._global.acquire(), self._timeout)

    async def acquire_user(self, identity_key: str):
        return await wait_for(self._user[identity_key].acquire(), self._timeout)

    async def acquire_branch(self, branch_id: int):
        return await wait_for(self._branch[branch_id].acquire(), self._timeout)

    async def acquire_sector(self, sector_id: int):
        return await wait_for(self._sector[sector_id].acquire(), self._timeout)

    async def acquire_session(self, session_id: str):
        return await wait_for(self._session[session_id].acquire(), self._timeout)

    def release_global(self):
        self._global.release()

    def release_user(self, identity_key: str):
        self._user[identity_key].release()

    def release_branch(self, branch_id: int):
        self._branch[branch_id].release()

    def release_sector(self, sector_id: int):
        self._sector[sector_id].release()

    def release_session(self, session_id: str):
        self._session[session_id].release()


class ConnectionManager:
    """
    Multi-dimensional connection manager with sharded locks.

    Forward indexes: identity -> connections, branch -> connections, sector -> waiters, session -> diners
    Inverse indexes: ws -> identity, ws -> branch, ws -> sector, ws -> session, ws -> metadata
    """

    def __init__(self, max_total: int = 1000, max_per_user: int = 3, lock_timeout: float = 5.0):
        self._max_total = max_total
        self._max_per_user = max_per_user
        self._locks = ShardedLocks(timeout=lock_timeout)

        # Forward indexes
        self._identity_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._branch_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._sector_waiters: dict[int, set[WebSocket]] = defaultdict(set)
        self._session_diners: dict[str, set[WebSocket]] = defaultdict(set)

        # Inverse indexes
        self._ws_to_identity: dict[WebSocket, str] = {}
        self._ws_to_branch: dict[WebSocket, int] = {}
        self._ws_to_sector: dict[WebSocket, int] = {}
        self._ws_to_session: dict[WebSocket, str] = {}
        self._ws_to_metadata: dict[WebSocket, ConnectionMetadata] = {}

        self._total_connections: int = 0

    @property
    def total_connections(self) -> int:
        return self._total_connections

    async def connect(self, ws: WebSocket, metadata: ConnectionMetadata) -> WebSocket | None:
        """
        Register a new connection. Returns the WebSocket that was displaced (if any)
        due to per-user limit, or None.

        Raises:
            ServerFullError: If total connections >= max_total
            LockTimeoutError: If any lock acquisition times out
        """
        displaced: WebSocket | None = None
        identity_key = metadata.identity_key

        # Level 0: Global lock
        try:
            await self._locks.acquire_global()
            if self._total_connections >= self._max_total:
                self._locks.release_global()
                raise ServerFullError(f"Max connections reached: {self._max_total}")
            self._total_connections += 1
            self._locks.release_global()
        except TimeoutError:
            raise LockTimeoutError("global_lock")

        # Level 1: User lock
        try:
            await self._locks.acquire_user(identity_key)
            conns = self._identity_connections[identity_key]
            if len(conns) >= self._max_per_user:
                oldest = min(conns, key=lambda w: self._ws_to_metadata[w].connected_at)
                displaced = oldest
                conns.discard(oldest)
            conns.add(ws)
            self._ws_to_identity[ws] = identity_key
            self._locks.release_user(identity_key)
        except TimeoutError:
            await self._locks.acquire_global()
            self._total_connections -= 1
            self._locks.release_global()
            raise LockTimeoutError("user_lock")

        # Level 2: Branch lock
        try:
            await self._locks.acquire_branch(metadata.branch_id)
            self._branch_connections[metadata.branch_id].add(ws)
            self._ws_to_branch[ws] = metadata.branch_id
            self._locks.release_branch(metadata.branch_id)
        except TimeoutError:
            raise LockTimeoutError("branch_lock")

        # Level 3: Sector or Session lock
        if metadata.role == "waiter" and metadata.sector_id is not None:
            try:
                await self._locks.acquire_sector(metadata.sector_id)
                self._sector_waiters[metadata.sector_id].add(ws)
                self._ws_to_sector[ws] = metadata.sector_id
                self._locks.release_sector(metadata.sector_id)
            except TimeoutError:
                raise LockTimeoutError("sector_lock")

        if metadata.role == "diner" and metadata.session_id is not None:
            try:
                await self._locks.acquire_session(metadata.session_id)
                self._session_diners[metadata.session_id].add(ws)
                self._ws_to_session[ws] = metadata.session_id
                self._locks.release_session(metadata.session_id)
            except TimeoutError:
                raise LockTimeoutError("session_lock")

        self._ws_to_metadata[ws] = metadata

        logger.info(
            "connection_registered",
            extra={
                "identity": identity_key,
                "branch_id": metadata.branch_id,
                "role": metadata.role,
                "total": self._total_connections,
            },
        )

        return displaced

    async def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket from ALL indexes. Idempotent."""
        metadata = self._ws_to_metadata.pop(ws, None)
        if metadata is None:
            return

        identity_key = metadata.identity_key

        try:
            await self._locks.acquire_global()
            self._total_connections = max(0, self._total_connections - 1)
            self._locks.release_global()
        except TimeoutError:
            logger.warning("disconnect: global_lock timeout")

        try:
            await self._locks.acquire_user(identity_key)
            self._identity_connections[identity_key].discard(ws)
            self._ws_to_identity.pop(ws, None)
            if not self._identity_connections[identity_key]:
                del self._identity_connections[identity_key]
            self._locks.release_user(identity_key)
        except TimeoutError:
            logger.warning("disconnect: user_lock timeout")

        branch_id = self._ws_to_branch.pop(ws, None)
        if branch_id is not None:
            try:
                await self._locks.acquire_branch(branch_id)
                self._branch_connections[branch_id].discard(ws)
                if not self._branch_connections[branch_id]:
                    del self._branch_connections[branch_id]
                self._locks.release_branch(branch_id)
            except TimeoutError:
                logger.warning("disconnect: branch_lock timeout")

        sector_id = self._ws_to_sector.pop(ws, None)
        if sector_id is not None:
            try:
                await self._locks.acquire_sector(sector_id)
                self._sector_waiters[sector_id].discard(ws)
                if not self._sector_waiters[sector_id]:
                    del self._sector_waiters[sector_id]
                self._locks.release_sector(sector_id)
            except TimeoutError:
                logger.warning("disconnect: sector_lock timeout")

        session_id = self._ws_to_session.pop(ws, None)
        if session_id is not None:
            try:
                await self._locks.acquire_session(session_id)
                self._session_diners[session_id].discard(ws)
                if not self._session_diners[session_id]:
                    del self._session_diners[session_id]
                self._locks.release_session(session_id)
            except TimeoutError:
                logger.warning("disconnect: session_lock timeout")

        logger.info(
            "connection_disconnected",
            extra={"identity": identity_key, "total": self._total_connections},
        )

    def get_metadata(self, ws: WebSocket) -> ConnectionMetadata | None:
        return self._ws_to_metadata.get(ws)

    def get_session_connections(self, session_id: str) -> set[WebSocket]:
        return self._session_diners.get(session_id, set()).copy()

    def get_branch_connections(self, branch_id: int) -> set[WebSocket]:
        return self._branch_connections.get(branch_id, set()).copy()

    def get_sector_connections(self, sector_id: int) -> set[WebSocket]:
        return self._sector_waiters.get(sector_id, set()).copy()

    def get_all_connections(self) -> list[tuple[WebSocket, ConnectionMetadata]]:
        """For heartbeat/cleanup iteration. Returns a snapshot."""
        return list(self._ws_to_metadata.items())

    def update_heartbeat(self, ws: WebSocket) -> None:
        meta = self._ws_to_metadata.get(ws)
        if meta:
            meta.last_heartbeat = datetime.utcnow()

    def update_reauth(self, ws: WebSocket) -> None:
        meta = self._ws_to_metadata.get(ws)
        if meta:
            meta.last_reauth = datetime.utcnow()


class ServerFullError(Exception):
    pass

class LockTimeoutError(Exception):
    def __init__(self, lock_name: str):
        self.lock_name = lock_name
        super().__init__(f"Lock acquisition timeout: {lock_name}")
```

---

## 3. WebSocket Auth Strategy Design

```python
# ws_gateway/auth/strategy.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from fastapi import WebSocket

@dataclass
class AuthResult:
    """Result of WebSocket authentication."""
    authenticated: bool
    user_id: int | None = None
    diner_id: str | None = None
    tenant_id: int | None = None
    branch_id: int | None = None
    role: str | None = None
    session_id: str | None = None
    table_id: int | None = None
    sector_id: int | None = None
    error: str | None = None

class WebSocketAuthStrategy(ABC):
    """Abstract strategy for WebSocket authentication."""

    @abstractmethod
    async def authenticate(self, ws: WebSocket) -> AuthResult:
        ...

    @abstractmethod
    async def revalidate(self, ws: WebSocket, metadata: 'ConnectionMetadata') -> bool:
        ...

    @abstractmethod
    def reauth_interval_seconds(self) -> int:
        ...


class StaffJWTStrategy(WebSocketAuthStrategy):
    """
    Authenticates staff via JWT in query parameter.
    Revalidates every 5 minutes by checking expiry + Redis blacklist.
    """

    def __init__(self, jwt_service, redis_blacklist, reauth_seconds: int = 300):
        self._jwt = jwt_service
        self._blacklist = redis_blacklist
        self._reauth_seconds = reauth_seconds

    async def authenticate(self, ws: WebSocket) -> AuthResult:
        token = ws.query_params.get("token")
        if not token:
            return AuthResult(authenticated=False, error="missing_token")

        try:
            claims = self._jwt.decode(token)
        except ExpiredTokenError:
            return AuthResult(authenticated=False, error="token_expired")
        except InvalidTokenError as e:
            return AuthResult(authenticated=False, error=f"invalid_token: {e}")

        jti = claims.get("jti")
        if jti and await self._blacklist.is_blacklisted(jti):
            return AuthResult(authenticated=False, error="token_revoked")

        role = claims.get("role", "").lower()
        endpoint = ws.scope.get("path", "")
        if not self._role_matches_endpoint(role, endpoint):
            return AuthResult(authenticated=False, error=f"role_{role}_not_allowed_on_{endpoint}")

        return AuthResult(
            authenticated=True,
            user_id=claims["sub"],
            tenant_id=claims["tenant_id"],
            branch_id=claims["branch_id"],
            role=role,
            sector_id=claims.get("sector_id"),
        )

    async def revalidate(self, ws: WebSocket, metadata) -> bool:
        token = ws.query_params.get("token")
        if not token:
            return False
        try:
            claims = self._jwt.decode(token)
            jti = claims.get("jti")
            if jti and await self._blacklist.is_blacklisted(jti):
                return False
            return True
        except Exception:
            return False

    def reauth_interval_seconds(self) -> int:
        return self._reauth_seconds

    @staticmethod
    def _role_matches_endpoint(role: str, endpoint: str) -> bool:
        allowed = {
            "/ws/waiter": {"waiter", "manager", "admin"},
            "/ws/kitchen": {"kitchen", "chef", "manager", "admin"},
            "/ws/admin": {"admin", "manager", "owner"},
        }
        return role in allowed.get(endpoint, set())


class DinerTableTokenStrategy(WebSocketAuthStrategy):
    """
    Authenticates diners via HMAC table token in query parameter.
    Revalidates every 30 minutes by checking session is still active.
    """

    def __init__(self, hmac_service, session_repo, reauth_seconds: int = 1800):
        self._hmac = hmac_service
        self._session_repo = session_repo
        self._reauth_seconds = reauth_seconds

    async def authenticate(self, ws: WebSocket) -> AuthResult:
        token = ws.query_params.get("table_token")
        if not token:
            return AuthResult(authenticated=False, error="missing_table_token")

        try:
            token_data = self._hmac.verify(token)
        except InvalidTokenError as e:
            return AuthResult(authenticated=False, error=f"invalid_table_token: {e}")

        session_id = token_data["session_id"]
        table_id = token_data["table_id"]
        diner_id = token_data.get("diner_id")
        tenant_id = token_data["tenant_id"]
        branch_id = token_data["branch_id"]

        session = await self._session_repo.get_by_id(session_id)
        if not session or session.status != "active":
            return AuthResult(authenticated=False, error="session_not_active")

        return AuthResult(
            authenticated=True,
            diner_id=diner_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            role="diner",
            session_id=session_id,
            table_id=table_id,
        )

    async def revalidate(self, ws: WebSocket, metadata) -> bool:
        session = await self._session_repo.get_by_id(metadata.session_id)
        return session is not None and session.status == "active"

    def reauth_interval_seconds(self) -> int:
        return self._reauth_seconds


class OriginValidator:
    """Validates Origin header against whitelist before WebSocket upgrade."""

    def __init__(self, whitelist: list[str]):
        self._whitelist = set(whitelist)

    def is_allowed(self, origin: str | None) -> bool:
        if not origin:
            return False
        return origin in self._whitelist


def get_auth_strategy(path: str, dependencies) -> WebSocketAuthStrategy:
    """Factory function to select strategy based on endpoint path."""
    if path in ("/ws/waiter", "/ws/kitchen", "/ws/admin"):
        return StaffJWTStrategy(
            jwt_service=dependencies.jwt_service,
            redis_blacklist=dependencies.redis_blacklist,
            reauth_seconds=dependencies.config.ws_staff_reauth_seconds,
        )
    elif path == "/ws/diner":
        return DinerTableTokenStrategy(
            hmac_service=dependencies.hmac_service,
            session_repo=dependencies.session_repo,
            reauth_seconds=dependencies.config.ws_diner_reauth_seconds,
        )
    else:
        raise ValueError(f"Unknown WebSocket path: {path}")
```

---

## 4. Heartbeat Manager Design

```python
# ws_gateway/core/heartbeat.py

import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("ws_gateway.heartbeat")

class HeartbeatManager:
    """
    Manages heartbeat pings and zombie detection.

    - Sends PING to all connections every `ping_interval` seconds.
    - Runs cleanup every `cleanup_interval` seconds (2-phase: identify + close).
    - Zombie threshold: connections with no PONG for `zombie_timeout` seconds.
    """

    def __init__(
        self,
        connection_manager: 'ConnectionManager',
        ping_interval: int = 30,
        zombie_timeout: int = 60,
        cleanup_interval: int = 30,
    ):
        self._cm = connection_manager
        self._ping_interval = ping_interval
        self._zombie_timeout = zombie_timeout
        self._cleanup_interval = cleanup_interval
        self._ping_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None

    async def start(self):
        self._ping_task = asyncio.create_task(self._ping_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("heartbeat_manager_started", extra={
            "ping_interval": self._ping_interval,
            "zombie_timeout": self._zombie_timeout,
            "cleanup_interval": self._cleanup_interval,
        })

    async def stop(self):
        if self._ping_task:
            self._ping_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def _ping_loop(self):
        while True:
            await asyncio.sleep(self._ping_interval)
            connections = self._cm.get_all_connections()
            for ws, meta in connections:
                try:
                    await ws.send_json({"type": "PING", "timestamp": datetime.utcnow().isoformat()})
                except Exception:
                    pass

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(self._cleanup_interval)
            now = datetime.utcnow()
            threshold = now - timedelta(seconds=self._zombie_timeout)

            # Phase 1: Identify zombies (no locks)
            connections = self._cm.get_all_connections()
            zombies = [
                (ws, meta) for ws, meta in connections
                if meta.last_heartbeat < threshold
            ]

            if not zombies:
                continue

            logger.info(f"zombie_scan: found={len(zombies)}, total={len(connections)}")

            # Phase 2: Close zombies (with locks, re-verify)
            closed_count = 0
            for ws, meta in zombies:
                current_meta = self._cm.get_metadata(ws)
                if current_meta is None:
                    continue
                if current_meta.last_heartbeat >= threshold:
                    continue

                try:
                    await ws.close(code=4004, reason="heartbeat_timeout")
                except Exception:
                    pass

                await self._cm.disconnect(ws)
                closed_count += 1

            logger.info(
                "zombie_cleanup_complete",
                extra={
                    "identified": len(zombies),
                    "closed": closed_count,
                    "active_after": self._cm.total_connections,
                },
            )
```

---

## 5. Revalidation Manager Design

```python
# ws_gateway/core/reauth.py

import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("ws_gateway.reauth")

class ReauthManager:
    """
    Periodically revalidates auth for all active connections.
    Staff: every 5 min. Diners: every 30 min.
    """

    def __init__(self, connection_manager, auth_strategies: dict, check_interval: int = 60):
        self._cm = connection_manager
        self._strategies = auth_strategies
        self._check_interval = check_interval
        self._task: asyncio.Task | None = None

    async def start(self):
        self._task = asyncio.create_task(self._reauth_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()

    async def _reauth_loop(self):
        while True:
            await asyncio.sleep(self._check_interval)
            now = datetime.utcnow()
            connections = self._cm.get_all_connections()

            for ws, meta in connections:
                strategy = self._strategies.get(meta.auth_strategy)
                if not strategy:
                    continue

                interval = timedelta(seconds=strategy.reauth_interval_seconds())
                if now - meta.last_reauth < interval:
                    continue

                is_valid = await strategy.revalidate(ws, meta)
                if is_valid:
                    self._cm.update_reauth(ws)
                else:
                    close_code = 4001 if meta.auth_strategy == "staff_jwt" else 4003
                    try:
                        await ws.close(code=close_code, reason="reauth_failed")
                    except Exception:
                        pass
                    await self._cm.disconnect(ws)
                    logger.info("reauth_failed", extra={
                        "identity": meta.identity_key,
                        "strategy": meta.auth_strategy,
                        "close_code": close_code,
                    })
```

---

## 6. Redis Pub/Sub Manager Design

```python
# ws_gateway/core/pubsub.py

import asyncio
import json
import logging
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

logger = logging.getLogger("ws_gateway.pubsub")

class RedisPubSubManager:
    """
    Manages Redis Pub/Sub subscriptions for the gateway.

    Channel naming:
    - ws:branch:{branch_id}   -> all connections in a branch
    - ws:sector:{sector_id}   -> waiters in a sector
    - ws:session:{session_id} -> diners in a table session
    """

    def __init__(self, redis: Redis, connection_manager: 'ConnectionManager'):
        self._redis = redis
        self._cm = connection_manager
        self._pubsub: PubSub | None = None
        self._subscriptions: dict[str, set[str]] = {}
        self._listener_task: asyncio.Task | None = None
        self._reconnecting = False

    async def start(self):
        self._pubsub = self._redis.pubsub()
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("pubsub_manager_started")

    async def stop(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

    async def subscribe_connection(self, ws_metadata: 'ConnectionMetadata'):
        """Subscribe to all relevant channels for a connection."""
        channels = self._channels_for_metadata(ws_metadata)
        for channel in channels:
            if channel not in self._subscriptions:
                self._subscriptions[channel] = set()
                await self._pubsub.subscribe(channel)
                logger.debug(f"subscribed to channel: {channel}")
            self._subscriptions[channel].add(ws_metadata.identity_key)

    async def unsubscribe_connection(self, ws_metadata: 'ConnectionMetadata'):
        """Unsubscribe from channels if no more local subscribers."""
        channels = self._channels_for_metadata(ws_metadata)
        for channel in channels:
            if channel in self._subscriptions:
                self._subscriptions[channel].discard(ws_metadata.identity_key)
                if not self._subscriptions[channel]:
                    del self._subscriptions[channel]
                    await self._pubsub.unsubscribe(channel)
                    logger.debug(f"unsubscribed from channel: {channel}")

    async def publish(self, channel: str, message: dict):
        """Publish a message to a Redis channel."""
        await self._redis.publish(channel, json.dumps(message))

    async def _listen(self):
        """Listen for messages and route to local WebSockets."""
        while True:
            try:
                async for message in self._pubsub.listen():
                    if message["type"] != "message":
                        continue
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode("utf-8")
                    data = json.loads(message["data"])
                    await self._route_message(channel, data)
            except Exception as e:
                logger.error(f"pubsub_listener_error: {e}")
                if not self._reconnecting:
                    asyncio.create_task(self._reconnect())

    async def _route_message(self, channel: str, data: dict):
        """Route a Pub/Sub message to local WebSocket connections."""
        target_connections: set = set()

        if channel.startswith("ws:branch:"):
            branch_id = int(channel.split(":")[-1])
            target_connections = self._cm.get_branch_connections(branch_id)
        elif channel.startswith("ws:sector:"):
            sector_id = int(channel.split(":")[-1])
            target_connections = self._cm.get_sector_connections(sector_id)
        elif channel.startswith("ws:session:"):
            session_id = channel.split(":")[-1]
            target_connections = self._cm.get_session_connections(session_id)

        sender_id = data.get("meta", {}).get("sender_id")
        for ws in target_connections:
            meta = self._cm.get_metadata(ws)
            if meta and meta.identity_key == f"diner:{sender_id}":
                continue
            try:
                await ws.send_json(data)
            except Exception:
                pass

    async def _reconnect(self):
        """Reconnect to Redis with exponential backoff."""
        self._reconnecting = True
        delay = 1
        max_delay = 30
        while True:
            try:
                await asyncio.sleep(delay)
                self._pubsub = self._redis.pubsub()
                for channel in self._subscriptions:
                    await self._pubsub.subscribe(channel)
                self._listener_task = asyncio.create_task(self._listen())
                logger.info(f"pubsub_reconnected, channels={len(self._subscriptions)}")
                self._reconnecting = False
                return
            except Exception as e:
                logger.warning(f"pubsub_reconnect_failed: {e}, retry in {delay}s")
                delay = min(delay * 2, max_delay)

    @staticmethod
    def _channels_for_metadata(meta: 'ConnectionMetadata') -> list[str]:
        channels = [f"ws:branch:{meta.branch_id}"]
        if meta.sector_id is not None:
            channels.append(f"ws:sector:{meta.sector_id}")
        if meta.session_id is not None:
            channels.append(f"ws:session:{meta.session_id}")
        return channels
```

---

## 7. Event Routing Matrix

| Event | Published to Channel | Received by |
|-------|---------------------|-------------|
| `CART_ITEM_ADDED` | `ws:session:{session_id}` | All diners in session (except sender) |
| `CART_ITEM_UPDATED` | `ws:session:{session_id}` | All diners in session (except sender) |
| `CART_ITEM_REMOVED` | `ws:session:{session_id}` | All diners in session (except sender) |
| `CART_CLEARED` | `ws:session:{session_id}` | All diners in session |
| `CART_SYNC` | Direct WebSocket (not Pub/Sub) | Single diner who requested sync |
| `CONNECTED` | Direct WebSocket (not Pub/Sub) | Single connecting client |
| `ERROR` | Direct WebSocket (not Pub/Sub) | Single affected client |

---

## 8. DinerWebSocket Class Design (Frontend)

```typescript
// pwa_menu/src/lib/ws/DinerWebSocket.ts

export interface DinerWebSocketConfig {
  baseUrl: string;
  tableToken: string;
  maxReconnectAttempts: number;
  initialReconnectDelay: number;
  maxReconnectDelay: number;
  jitterPercent: number;
  heartbeatTimeout: number;
}

export type ConnectionState = "connecting" | "connected" | "disconnected" | "reconnecting";

export type WSEventType =
  | "CONNECTED"
  | "CART_ITEM_ADDED"
  | "CART_ITEM_UPDATED"
  | "CART_ITEM_REMOVED"
  | "CART_CLEARED"
  | "CART_SYNC"
  | "ERROR"
  | "PING";

export interface WSMessage<T = unknown> {
  type: WSEventType;
  payload: T;
  meta: {
    id: string;
    timestamp: string;
    sender_id: string;
    session_id: string;
  };
}

type EventHandler<T = unknown> = (message: WSMessage<T>) => void;

export class DinerWebSocket {
  private ws: WebSocket | null = null;
  private config: Required<DinerWebSocketConfig>;
  private state: ConnectionState = "disconnected";
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setTimeout> | null = null;
  private handlers: Map<WSEventType, Set<EventHandler>> = new Map();
  private stateChangeCallbacks: Set<(state: ConnectionState) => void> = new Set();

  constructor(config: DinerWebSocketConfig) {
    this.config = {
      maxReconnectAttempts: 50,
      initialReconnectDelay: 1000,
      maxReconnectDelay: 30000,
      jitterPercent: 0.2,
      heartbeatTimeout: 40000,
      ...config,
    };
  }

  connect(): void {
    if (this.state === "connected" || this.state === "connecting") return;

    this.setState("connecting");
    const url = `${this.config.baseUrl}/ws/diner?table_token=${encodeURIComponent(this.config.tableToken)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.setState("connected");
      this.reconnectAttempts = 0;
      this.startHeartbeatMonitor();
    };

    this.ws.onmessage = (event) => {
      const message: WSMessage = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      this.stopHeartbeatMonitor();
      if (event.code === 1000 || event.code === 4003) {
        this.setState("disconnected");
        return;
      }
      this.attemptReconnect();
    };

    this.ws.onerror = () => {};
  }

  disconnect(): void {
    this.reconnectAttempts = this.config.maxReconnectAttempts;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close(1000, "client_disconnect");
      this.ws = null;
    }
    this.setState("disconnected");
  }

  on<T = unknown>(type: WSEventType, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler as EventHandler);
    return () => this.handlers.get(type)?.delete(handler as EventHandler);
  }

  onStateChange(callback: (state: ConnectionState) => void): () => void {
    this.stateChangeCallbacks.add(callback);
    return () => this.stateChangeCallbacks.delete(callback);
  }

  getState(): ConnectionState {
    return this.state;
  }

  private handleMessage(message: WSMessage): void {
    if (message.type === "PING") {
      this.resetHeartbeatMonitor();
      this.ws?.send(JSON.stringify({ type: "PONG", timestamp: new Date().toISOString() }));
      return;
    }

    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => handler(message));
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.setState("disconnected");
      return;
    }

    this.setState("reconnecting");
    const delay = this.calculateDelay();
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private calculateDelay(): number {
    const base = Math.min(
      this.config.initialReconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.config.maxReconnectDelay
    );
    const jitter = base * this.config.jitterPercent * (Math.random() * 2 - 1);
    return Math.max(0, base + jitter);
  }

  private startHeartbeatMonitor(): void {
    this.resetHeartbeatMonitor();
  }

  private resetHeartbeatMonitor(): void {
    this.stopHeartbeatMonitor();
    this.heartbeatTimer = setTimeout(() => {
      this.ws?.close(4004, "heartbeat_timeout");
    }, this.config.heartbeatTimeout);
  }

  private stopHeartbeatMonitor(): void {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private setState(newState: ConnectionState): void {
    if (this.state === newState) return;
    this.state = newState;
    this.stateChangeCallbacks.forEach((cb) => cb(newState));
  }
}
```

---

## 9. tableStore Architecture (Zustand) — Summary

**File split**: `pwa_menu/src/features/table/store/` with 4 files:
- `types.ts`: CartItem, CartItemInput, CartItemUpdate, CartState, CartActions, DinerSummary, ModifierSelection
- `helpers.ts`: LRUCache class (100 entries, 5s TTL), mergeCartState (server-authoritative), generateTempId (negative timestamps), calculateSubtotal, createDinerSummaries
- `selectors.ts`: selectAllItems, selectItemsByDiner(dinerId), selectItemCount, selectTotalCents, selectDinerSummaries, selectDinerSubtotal(dinerId), selectIsLoading, selectIsSyncing, selectError, selectItemById(itemId), selectHasPendingMutations
- `store.ts`: Zustand create with initialState + actions (addItem, updateItem, removeItem, syncFromServer, handleRemoteEvent, initialize, reset)

**Optimistic update pattern**:
1. Snapshot current items array
2. Apply optimistic mutation to store (instant UI update)
3. Store snapshot in pendingMutations Map keyed by mutationId (UUID)
4. Call backend API
5. On success: replace temp data with server response, delete from pendingMutations
6. On failure: restore snapshot from pendingMutations, set error message

**CartItem composite key**: (session_id, diner_id, product_id). Adding same product twice increments quantity.

**Temp IDs**: Negative numbers generated as `-(Date.now() + random)`. Server response replaces temp with real server-assigned ID.

---

## 10. useCartSync Hook Design — Summary

File: `pwa_menu/src/features/table/hooks/useCartSync.ts`

**Responsibilities**:
1. Initialize store with sessionId on mount
2. Subscribe to DinerWebSocket events (CART_ITEM_ADDED/UPDATED/REMOVED, CART_CLEARED, CART_SYNC) -> forward to handleRemoteEvent
3. On connection state change to "connected" -> debounce 1s -> fetch full cart from REST API -> mergeCartState (server wins)
4. LRU cache (100 entries, 5s TTL) prevents redundant sync fetches
5. Initial sync on mount

**Deduplication**: Same product_id + diner_id within 300ms debounce window -> single mutation.

---

## 11. Sequence Diagrams — Key Flows

### 11.1 Diner Connection
Browser -> DinerWebSocket.connect() -> GET /ws/diner?table_token=T -> Gateway validates origin -> checks rate limit -> DinerTableTokenStrategy.authenticate() -> verifies HMAC + session active -> ConnectionManager.connect(ws, metadata) -> checks total < 1000, user < 3 -> adds to all indexes -> RedisPubSubManager.subscribe(session_id) -> 101 Upgrade -> sends CONNECTED message -> useCartSync triggers initial sync

### 11.2 Cart Add Item (Optimistic)
UI action -> tableStore.addItem() -> snapshot -> optimistic add (UI updates instantly) -> cartApi.POST /cart/items -> backend validates session/diner/product -> INSERT cart_item -> PUBLISH CART_ITEM_ADDED to ws:session:{id} -> REST returns 201 -> store replaces temp with server item -> Gateway routes pub/sub message to other diners in session -> other diners' handleRemoteEvent updates their stores

### 11.3 Reconnection + Sync
Network loss -> DinerWebSocket.onclose -> state: reconnecting -> exponential backoff (1s, 2s, 4s...) -> reconnect succeeds -> state: connected -> useCartSync detects state change -> debounce 1s -> GET /api/sessions/{id}/cart -> mergeCartState(local, server) -> server wins on conflicts -> UI updated

---

## 12. Complete File Structure

### Backend ws_gateway/
```
ws_gateway/
├── pyproject.toml
├── Dockerfile
├── ws_gateway/
│   ├── __init__.py
│   ├── main.py                        # FastAPI app, lifespan, health
│   ├── config.py                      # GatewaySettings (Pydantic Settings)
│   ├── dependencies.py                # DI container
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── strategy.py                # ABC + StaffJWTStrategy + DinerTableTokenStrategy
│   │   ├── origin.py                  # OriginValidator
│   │   └── rate_limiter.py            # WS connection rate limiter
│   ├── core/
│   │   ├── __init__.py
│   │   ├── connection_manager.py      # ConnectionManager + ShardedLocks + ConnectionMetadata
│   │   ├── heartbeat.py               # HeartbeatManager (ping loop + cleanup loop)
│   │   ├── reauth.py                  # ReauthManager (periodic revalidation)
│   │   └── pubsub.py                  # RedisPubSubManager
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── waiter.py                  # /ws/waiter handler
│   │   ├── kitchen.py                 # /ws/kitchen handler
│   │   ├── admin.py                   # /ws/admin handler
│   │   └── diner.py                   # /ws/diner handler
│   ├── events/
│   │   ├── __init__.py
│   │   └── types.py                   # Event constants + envelope builder
│   └── middleware/
│       ├── __init__.py
│       └── logging.py                 # Structured logging
```

### Shared additions
```
shared/shared/models/room/cart_item.py     # CartItem model
shared/shared/repositories/cart_repository.py  # CartRepository
shared/shared/schemas/cart.py              # Pydantic schemas
shared/shared/events/__init__.py           # Events module
shared/shared/events/cart_events.py        # Cart event builders
```

### REST API additions
```
rest_api/app/routers/cart.py               # Cart endpoints
rest_api/app/services/cart_service.py      # Cart business logic
rest_api/app/schemas/cart.py               # Request/response schemas
```

### Frontend pwa_menu/
```
pwa_menu/src/lib/ws/DinerWebSocket.ts      # WS client class
pwa_menu/src/lib/ws/types.ts               # WS types
pwa_menu/src/features/table/store/types.ts
pwa_menu/src/features/table/store/helpers.ts
pwa_menu/src/features/table/store/selectors.ts
pwa_menu/src/features/table/store/store.ts
pwa_menu/src/features/table/hooks/useCartSync.ts
pwa_menu/src/features/table/api/cartApi.ts
pwa_menu/src/features/table/components/CartPanel.tsx
pwa_menu/src/features/table/components/CartItemCard.tsx
pwa_menu/src/features/table/components/DinerSection.tsx
pwa_menu/src/features/table/components/CartSummary.tsx
pwa_menu/src/features/table/components/ConnectionStatus.tsx
```

---

## 13. Database Schema

```sql
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES table_sessions(id) ON DELETE CASCADE,
    diner_id UUID NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    notes TEXT,
    modifiers JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, diner_id, product_id)
);
CREATE INDEX idx_cart_items_session ON cart_items(session_id);
CREATE INDEX idx_cart_items_diner ON cart_items(session_id, diner_id);
```

**SQLAlchemy model**: `shared/shared/models/room/cart_item.py` -- CartItem with PgUUID session_id, ForeignKey to table_sessions(id) ON DELETE CASCADE, ForeignKey to products(id), JSONB modifiers, UniqueConstraint on (session_id, diner_id, product_id), CheckConstraint quantity > 0.

---

## 14. New Environment Variables

```env
WS_MAX_CONNECTIONS=1000
WS_MAX_PER_USER=3
WS_HEARTBEAT_INTERVAL=30
WS_HEARTBEAT_TIMEOUT=60
WS_CLEANUP_INTERVAL=30
WS_ORIGIN_WHITELIST=http://localhost:5173,http://localhost:5174
WS_STAFF_REAUTH_SECONDS=300
WS_DINER_REAUTH_SECONDS=1800
WS_CONNECTION_RATE_LIMIT=10
WS_MESSAGE_RATE_LIMIT=30
CART_ENABLED=true
CART_RATE_LIMIT_PER_DINER=10
```
