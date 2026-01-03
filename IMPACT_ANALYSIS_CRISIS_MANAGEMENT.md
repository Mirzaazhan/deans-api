# Assignment 2: Execution-Based Call Graph Impact Analysis
**Name:** [Your Name]  
**Repository:** deans-api  
**Target Module:** `api/models/Crisis.py` (lines 166-261), `api/views.py`, `api/serializer.py`  
**Graph Selected:** Call Graph (functions/methods and runtime interactions)

---

## 1. Addressed Component / Module (1 mark)

**Focus:**  
This analysis targets the *Crisis Management Flow* in the backend API, specifically:
- The signal handler `trigger()` function in `api/models/Crisis.py` (lines 166-261)
- API view classes in `api/views.py` that trigger crisis save operations
- Serialization logic in `api/serializer.py` used for WebSocket broadcasting

This module governs the backend processing flow when a crisis is created or updated, managing:
- Social media notifications (Facebook, Twitter)
- Dispatch notifications (SMS/WhatsApp) for dispatched crises
- WebSocket real-time updates to connected clients

---

## 2. Call Graph (Execution-Based) and Completeness (3 marks)

### A. **Starting Impact Set (SIS), Justification**

**SIS:** `trigger()` function (Crisis.py:166)  
*Reasoning:* According to Chapter 6, the SIS is the first executed function in the relevant execution path. In this backend flow, `trigger()` is a Django post_save signal handler that is automatically invoked whenever a `Crisis` model instance is saved. It is the entry point for all post-save processing logic, including social media publishing, dispatch notifications, and WebSocket broadcasting. All subsequent runtime behavior in the Crisis Management Flow originates from this signal handler. Therefore, it correctly represents the SIS.

---

### B. **Identified Call Graph Nodes (Functions / Methods)**

Below are the explicit nodes in the call graph. Each node represents a callable unit that executes at runtime.

#### 1. Entry / Signal Handler Nodes

- **N1:** `trigger()` (Crisis.py:166) - SIS, Django post_save signal handler

#### 2. Data Retrieval / Query Nodes

- **N2:** `Crisis.objects.get(pk=instance.pk)` (Crisis.py:171) - Retrieves crisis instance from database

#### 3. Social Media Processing Nodes

- **N3:** `construct_social_media_data(this_crisis)` (Crisis.py:172) - Constructs social media payload
- **N4:** `Crisis.objects.filter()` / `Crisis.objects.exclude()` (within construct_social_media_data) - Queries for recent resolved and active crises
- **N5:** `this_crisis.crisis_type.all()` - Accesses ManyToMany relationship for crisis types
- **N6:** `this_crisis.crisis_assistance.all()` - Accesses ManyToMany relationship for assistance types
- **N7:** `requests.post()` - Social media notification API call (Crisis.py:181)

#### 4. Dispatch Processing Nodes (Conditional)

- **N8:** Conditional check `if this_crisis.crisis_status == "DP"` (Crisis.py:192)
- **N9:** `json.loads(this_crisis.phone_number_to_notify)` (Crisis.py:195) - Parses phone numbers JSON
- **N10:** `this_crisis.crisis_type.all()` (Crisis.py:203) - Retrieves crisis types for dispatch message
- **N11:** `this_crisis.crisis_assistance.all()` (Crisis.py:209) - Retrieves assistance types for dispatch message
- **N12:** `requests.post()` - Dispatch notification API call (Crisis.py:234) - Executed per phone number in loop

#### 5. WebSocket Broadcasting Nodes

- **N13:** `Crisis.objects.all()` (Crisis.py:250) - Queries all crises for WebSocket update
- **N14:** `CrisisSerializer(queryset, many=True)` (Crisis.py:252) - Serializes crisis data
- **N15:** `Response(serializer.data)` (Crisis.py:253) - Creates DRF Response object
- **N16:** `channels.layers.get_channel_layer()` (Crisis.py:254) - Gets Django Channels layer
- **N17:** `async_to_sync(channel_layer.group_send)()` (Crisis.py:255) - Broadcasts to WebSocket group
- **N18:** `CrisesConsumer.crises_update()` (consumers.py:39) - WebSocket consumer receives message

#### 6. View Layer Nodes (Entry Points to SIS)

- **N19:** `CrisisViewSet.create()` (views.py:42) - Creates crisis via DRF ViewSet
- **N20:** `CrisisViewSet.update()` (views.py:42) - Updates crisis via DRF ViewSet
- **N21:** `CrisisUpdateView.put()` (views.py:77) - Full update via generic view
- **N22:** `CrisisPartialUpdateView.put()` (views.py:87) - Partial update via generic view

#### 7. Serialization Nodes

- **N23:** `CrisisSerializer.serialize()` - DRF serializer serialization process
- **N24:** `CrisisSerializer.to_representation()` - Converts model instance to dict
- **N25:** Access to `CrisisType` model fields (via ManyToMany)
- **N26:** Access to `CrisisAssistance` model fields (via ManyToMany)

### C. **Call Graph Edges (Invocation Relationships)**

Each arrow below represents "may invoke during execution", exactly as defined in the lecture call graph.

#### 1. View to Model Save (Entry to Signal)

- **N19 → N1:** `CrisisViewSet.create()` saves Crisis instance, triggers `trigger()` signal
- **N20 → N1:** `CrisisViewSet.update()` saves Crisis instance, triggers `trigger()` signal
- **N21 → N1:** `CrisisUpdateView.put()` saves Crisis instance, triggers `trigger()` signal
- **N22 → N1:** `CrisisPartialUpdateView.put()` saves Crisis instance, triggers `trigger()` signal

#### 2. Signal Handler Execution Phase

- **N1 → N2:** `trigger()` retrieves crisis instance from database
- **N1 → N3:** `trigger()` calls `construct_social_media_data()`

#### 3. Social Media Data Construction

- **N3 → N4:** `construct_social_media_data()` queries for recent resolved and active crises
- **N3 → N5:** Accesses `crisis_type` ManyToMany relationship
- **N3 → N6:** Accesses `crisis_assistance` ManyToMany relationship
- **N1 → N7:** `trigger()` makes HTTP POST request to notification service

#### 4. Dispatch Processing Flow (Conditional)

- **N1 → N8:** Conditional check for dispatched crisis status
- **N8 → N9:** If dispatched, parses phone numbers JSON
- **N8 → N10:** Retrieves crisis types for message construction
- **N8 → N11:** Retrieves assistance types for message construction
- **N8 → N12:** Makes HTTP POST request per phone number (loop)

#### 5. WebSocket Broadcasting Flow

- **N1 → N13:** `trigger()` queries all crises
- **N13 → N14:** Creates `CrisisSerializer` instance with queryset
- **N14 → N23:** Serializer begins serialization process
- **N23 → N24:** `to_representation()` converts to dict
- **N24 → N25:** Accesses `CrisisType` model fields
- **N24 → N26:** Accesses `CrisisAssistance` model fields
- **N14 → N15:** Creates `Response` object with serialized data
- **N1 → N16:** Gets Django Channels layer
- **N1 → N17:** Broadcasts message to WebSocket group "crises"
- **N17 → N18:** `CrisesConsumer.crises_update()` receives and processes message

---

## 3. Impact / Insights Gained (1 mark)

### A. **Candidate Impact Set (CIS)**

*Per Chapter 6, CIS is the closure of all nodes (functions/components) directly or indirectly invoked from the SIS (`trigger()`). This includes:*
- All runtime database queries and ORM operations triggered by the signal handler
- All external API calls to notification services (social media and dispatch)
- All serialization logic used for WebSocket broadcasting
- All view classes that trigger crisis save operations (entry points)
- All model relationships accessed during processing (CrisisType, CrisisAssistance)

**Direct Impacts:**  
- Any modification to `trigger()` (SIS) immediately impacts social media publishing, dispatch notifications, and WebSocket broadcasting flows.
- Changes to `construct_social_media_data()` affect social media payload structure and notification content.
- Modifications to WebSocket broadcasting section (lines 248-260) affect real-time updates to connected clients.

**Indirect Impacts (Ripple Effect):**  
- Changing `CrisisSerializer` field definitions can break WebSocket message format, causing frontend parsing errors.
- Modifying view classes (CrisisViewSet, CrisisUpdateView) can affect when and how the signal is triggered, potentially changing execution frequency or context.
- Changes to `CrisisType` or `CrisisAssistance` model fields propagate through ManyToMany relationships, affecting serialization and message construction.
- External API contract changes (notification service endpoints) can cause runtime failures if not synchronized.
- Database query optimizations or changes to Crisis model can affect performance and data consistency across all three flows (social media, dispatch, WebSocket).

### B. **Insights and Issues**

- **High Fan-Out:** The SIS (`trigger()`) triggers three independent processing flows (social media, dispatch, WebSocket), each with multiple database queries and external API calls. This creates significant fan-out and potential failure points.

- **Tight Coupling:** The signal handler directly imports and uses `CrisisSerializer` and `Response` from DRF (line 251-253), creating tight coupling between the model layer and serialization/response layers. This violates separation of concerns.

- **Performance Issues:** 
  - Line 250: `Crisis.objects.all()` fetches ALL crises for every save operation, regardless of whether data changed. This is inefficient and can cause performance degradation as crisis count grows.
  - Multiple database queries within `construct_social_media_data()` (lines 74-75) and within the signal handler create N+1 query potential.

- **Error Handling Gaps:** 
  - Social media API call (line 181) has no error handling - failures are silently logged but don't prevent execution.
  - Dispatch notification loop (lines 232-240) has generic exception handling that swallows all errors with "It is ok." message, masking critical failures.
  - WebSocket broadcasting (lines 248-260) has exception handling but error message "Human lives at risk!" suggests criticality without proper alerting mechanism.

- **Code Smell:** Line 253 creates a `Response` object but only uses `response.data` - this is unnecessary overhead and misuse of DRF Response class outside of view context.

- **Ripple Effect Risk:** Changes to Crisis model fields (e.g., adding/removing fields) will propagate through:
  - `construct_social_media_data()` payload construction
  - Dispatch message construction
  - `CrisisSerializer` field definitions
  - WebSocket message format

### C. **Refactoring Recommendations**

- **Reduce Fan-Out:** Extract social media, dispatch, and WebSocket logic into separate service classes. This isolates concerns and makes each flow independently testable and maintainable.

- **Optimize Database Queries:** 
  - Use `select_related()` and `prefetch_related()` for ManyToMany relationships to reduce query count.
  - For WebSocket broadcasting, only fetch and broadcast changed crisis data, not all crises.
  - Cache frequently accessed data (crisis types, assistance types) to reduce database load.

- **Improve Error Handling:** 
  - Implement structured error handling with proper logging levels (error, warning, info).
  - Add retry logic for external API calls with exponential backoff.
  - Implement circuit breaker pattern for notification service to prevent cascade failures.

- **Decouple Dependencies:** 
  - Remove direct DRF imports (`Response`, `CrisisSerializer`) from model layer.
  - Create a WebSocket service abstraction that handles serialization internally.
  - Use dependency injection for external service clients.

- **Minimize Ripple Effect:** 
  - Create data transfer objects (DTOs) for crisis data to isolate model changes from serialization and message construction.
  - Use versioned API contracts for WebSocket messages to support backward compatibility.
  - Implement change detection to only process and broadcast actual data changes.

- **Improve Maintainability:** 
  - Add comprehensive unit tests for each processing flow.
  - Implement monitoring and alerting for external API call failures.
  - Document expected behavior and failure modes for each flow.

---

**Keywords:** SIS, CIS, execution flow, call graph, ripple effect, Django signals, WebSocket, serialization, fan-out, maintainability, error handling

