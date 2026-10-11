# Architecture and System Flow Diagrams

This document specifies the technical architecture, execution flows, and state machine transitions for the RoamAgent autonomous travel planning platform.

---

## 1. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Client_Layer["Frontend Application (React + Vite + TypeScript)"]
        UI_Prompt["Prompt Interface<br/>(SpeechRecognition / Text Input)"]
        UI_Review["Budget Review View<br/>(Slider Adjustment & Parameter Confirmation)"]
        UI_Itinerary["Itinerary View<br/>(Day-by-Day Timeline & Budget Ledger)"]
        UI_Booking["In-App Booking Engine<br/>(Bus PNR Voucher & Hotel Reservation)"]
        UI_Map["Map Modal<br/>(Leaflet + OpenStreetMap + OSRM Engine)"]
        UI_History["Trip History View<br/>(Session Recovery & Long-Press Deletion)"]
        Auth_State["AuthContext & ApiClient<br/>(JWT Bearer, Resilient Refresh, Mutex)"]
    end

    subgraph API_Gateway["FastAPI Gateway (Uvicorn Server: 8000)"]
        MW_CORS["CORS & Auth Middleware"]
        Route_Auth["/api/v1/auth<br/>(Register, Login, Refresh, Me)"]
        Route_Intent["/api/v1/trip/intent<br/>(Phase 1: Intent Extraction & Budget Caps)"]
        Route_Plan["/api/v1/trip/plan<br/>(Phase 2: Agentic Synthesis Execution)"]
        Route_History["/api/v1/trip/history<br/>(Session Management, Deletion)"]
    end

    subgraph LangGraph_Orchestrator["LangGraph StateGraph Engine"]
        State_Init["TravelPlanState Initialization<br/>(session_uuid, parameters, budgets)"]
        
        Node_Bus["Node 1: bus_search_node<br/>(Origin-Destination Match, Return Bus, Budget Fit)"]
        Node_Hotel["Node 2: hotel_search_node<br/>(City dest_id Resolution, Pricing Filter)"]
        Node_Places["Node 3: tourist_places_node<br/>(Landmark Extraction & Geo-Coordinates)"]
        Node_Synth["Node 4: synthesizer_node<br/>(Day-by-Day Schedule, Cost Audit, Savings)"]
        
        State_End["StateGraph END<br/>(Compiled Plan Response Data)"]
    end

    subgraph External_Integrations["External Services & Data Layer"]
        LLM_Groq["Groq Cloud LLM<br/>(Qwen Model API)"]
        API_Rapid["RapidAPI Booking.com<br/>(Live Hotel Inventory API)"]
        API_Wiki["Wikipedia Client<br/>(MediaWiki API + Geocoding)"]
        DB_Buses["Local Transit Database<br/>(data/buses.json)"]
        API_OSRM["OSRM Routing Server<br/>(project-osrm.org Road Polylines)"]
        DB_Postgres["Supabase PostgreSQL<br/>(Pooler 6543, Peewee ORM, TCP Keepalive)"]
    end

    %% Client to API Gateway
    UI_Prompt -->|"POST /trip/intent"| Route_Intent
    UI_Review -->|"POST /trip/plan"| Route_Plan
    UI_History -->|"GET /trip/history"| Route_History
    Auth_State -->|"Bearer JWT"| MW_CORS
    MW_CORS --> Route_Auth

    %% API Gateway to LangGraph and LLM
    Route_Intent -->|"Extract Parameters"| LLM_Groq
    Route_Intent -->|"Save INTENT_PARSED"| DB_Postgres
    Route_Plan --> State_Init

    %% LangGraph Pipeline
    State_Init --> Node_Bus
    Node_Bus -->|"Query Transit"| DB_Buses
    Node_Bus --> Node_Hotel
    Node_Hotel -->|"Fetch Hotels"| API_Rapid
    Node_Hotel --> Node_Places
    Node_Places -->|"Fetch Landmarks"| API_Wiki
    Node_Places --> Node_Synth
    Node_Synth -->|"Generate Coherent Plan"| LLM_Groq
    Node_Synth --> State_End

    %% Plan Output to Gateway & Client
    State_End -->|"Persist PLAN_GENERATED & Audit Log"| DB_Postgres
    State_End --> Route_Plan
    Route_Plan --> UI_Itinerary

    %% Interactive Client Modules
    UI_Itinerary --> UI_Booking
    UI_Itinerary --> UI_Map
    UI_Map -->|"Fetch Driving Directions"| API_OSRM
```

---

## 2. End-to-End Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Traveler
    participant UI as Mobile/Web Frontend
    participant Gateway as FastAPI Gateway
    participant Intent as Groq LLM (Intent Extraction)
    participant Graph as LangGraph State Machine
    participant BusRepo as Transit DB (buses.json)
    participant Rapid as RapidAPI (Booking.com)
    participant Wiki as Wikipedia Client
    participant Synth as Groq LLM (Synthesizer)
    participant DB as Supabase PostgreSQL

    %% Authentication & Intent Phase
    User->>UI: Speaks/types trip prompt
    UI->>Gateway: POST /api/v1/trip/intent (Prompt, Token)
    Gateway->>Intent: Extract travel constraints & budget
    Intent-->>Gateway: Parameters (from_city, to_city, dates, budget)
    Gateway->>Gateway: Calculate Budget Caps (30% Transit, 40% Hotel, 30% Reserve)
    Gateway->>DB: Persist TripSession (Status: INTENT_PARSED)
    Gateway-->>UI: Return Extracted Parameters & Caps
    UI-->>User: Render Budget Review & Parameter Confirmation

    %% Agentic Execution Phase
    User->>UI: Confirms parameters and clicks Generate Plan
    UI->>Gateway: POST /api/v1/trip/plan (Payload)
    Gateway->>Graph: Invoke travel_graph(initial_state)

    %% Node 1: Bus Search
    rect rgb(240, 245, 255)
    Note over Graph,BusRepo: Node 1: bus_search_node
    Graph->>BusRepo: Query transit matching route, bus_type, and budget
    BusRepo-->>Graph: Primary Bus + Alternatives (+ Return Bus if requested)
    end

    %% Node 2: Hotel Search
    rect rgb(250, 245, 240)
    Note over Graph,Rapid: Node 2: hotel_search_node
    Graph->>Rapid: Search city destination ID & check-in dates
    Rapid-->>Graph: Hotel candidates filtered by lodging budget cap
    end

    %% Node 3: Tourist Places
    rect rgb(240, 255, 245)
    Note over Graph,Wiki: Node 3: tourist_places_node
    Graph->>Wiki: Query top attractions & geographic coordinates
    Wiki-->>Graph: Landmark names, snippets, images, lat/long
    end

    %% Node 4: Synthesis
    rect rgb(255, 245, 250)
    Note over Graph,Synth: Node 4: synthesizer_node
    Graph->>Synth: Synthesize structured day-by-day plan with financial totals
    Synth-->>Graph: Chronological schedule, budget compliance, calculated savings
    end

    Graph-->>Gateway: Final State Response
    Gateway->>DB: Update TripSession (PLAN_GENERATED) & Write ApiLog
    Gateway-->>UI: Return Final Itinerary Plan

    %% Presentation & Interaction
    UI-->>User: Render Itinerary, Cost Ledger & OpenStreetMap
    opt In-App Booking Simulation
        User->>UI: Click Book Bus / Hotel
        UI->>UI: Generate Instant Mock PNR / Hotel Voucher
    end
    opt Interactive Mapping
        User->>UI: Open Map Modal
        UI->>Gateway: Request Route
        UI->>UI: Render OSRM Driving Polyline on Leaflet
    end
```

---

## 3. LangGraph State Machine Lifecycle

```mermaid
stateDiagram-v2
    [*] --> bus_search : Session State Initialized

    state bus_search {
        [*] --> FilterOutbound : Query Origin to Destination
        FilterOutbound --> CheckReturn : Transit Budget Checked
        CheckReturn --> SelectReturnBus : Return Required == true
        CheckReturn --> TransitFinalized : Return Required == false
        SelectReturnBus --> TransitFinalized : Combined Transit Cost Checked
        TransitFinalized --> [*]
    }

    bus_search --> hotel_search : Outbound + Return Bus Selected

    state hotel_search {
        [*] --> ResolveCityId : Destination Geocoding
        ResolveCityId --> QueryBookingApi : Date + Guest Parameters
        QueryBookingApi --> FilterPriceCap : Apply 40% Lodging Budget Cap
        FilterPriceCap --> SelectHotel : Primary + Alternative Selection
        SelectHotel --> [*]
    }

    hotel_search --> tourist_places : Hotel Selected

    state tourist_places {
        [*] --> QueryMediaWiki : Fetch Destination Attractions
        QueryMediaWiki --> ExtractCoordinates : Parse Geocoding Points
        ExtractCoordinates --> CompileLandmarks : Assemble Top Locations
        CompileLandmarks --> [*]
    }

    tourist_places --> synthesizer : Attractions Assembled

    state synthesizer {
        [*] --> ConstructPrompt : Merge Transit, Hotel, and Landmark Context
        ConstructPrompt --> InvokeGroqLLM : Structured Synthesis Request
        InvokeGroqLLM --> VerifyBudgetCompliance : Calculate Total vs Budget
        VerifyBudgetCompliance --> FinalStateCommitted : Append Ledger & Metrics
        FinalStateCommitted --> [*]
    }

    synthesizer --> [*] : Plan Ready (PLAN_GENERATED)
```

---

## 4. Architectural Boundaries and Component Responsibilities

### 4.1 Frontend Client (AgenticTravelTech_MobileApp)
- **Framework**: React 19, Vite, TypeScript.
- **State Management**: Context-based authentication with storage synchronization and auto-refresh locking.
- **Voice Pipeline**: Native browser SpeechRecognition API with automatic fallback to text input.
- **Map & Routing**: Leaflet integration consuming OpenStreetMap tiles and querying the OSRM routing engine for polyline driving geometries.
- **In-App Booking Engine**: Simulated PNR generator and lodging voucher confirmation modals avoiding third-party navigation redirects.

### 4.2 Backend Gateway (AgenticTravelTech)
- **Framework**: FastAPI with Uvicorn ASGI server.
- **Authentication**: JWT Bearer token security scheme (24-hour access token, 7-day refresh token).
- **Session Persistence**: Supabase PostgreSQL with Peewee ORM, connection pool keepalive (keepalives_idle=30, connect_timeout=10), and operational retry backoff.
- **Audit Logging**: Comprehensive ApiLog model capturing endpoint latency, HTTP status codes, and input/output payloads.

### 4.3 Multi-Agent State Machine (LangGraph)
- **State Schema**: `TravelPlanState` enforcing immutable key definitions across graph executions.
- **Bus Search Node**: Validates multi-passenger pricing, seat availability, arrival deadlines, and return journey constraints.
- **Hotel Search Node**: Resolves city codes against RapidAPI Booking.com, enforces a 40% lodging cap, and selects candidates based on star ratings and guest capacities.
- **Tourist Places Node**: Fetches verified landmarks, brief descriptions, and latitude/longitude coordinates via MediaWiki.
- **Synthesizer Node**: Invokes Groq Cloud Qwen model to generate day-by-day itineraries, calculate budget compliance, and format the final structured JSON response.
