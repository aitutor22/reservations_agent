# Unified Agents TODO

## Problem Statement
Currently, text mode and voice mode both use WebSocket but with different processing paths:
- **Text Mode**: Uses Assistants API with vector stores and custom agents
- **Voice Mode**: Uses WebSocket → Backend RealtimeAgent → OpenAI Realtime API
- **Issue**: Can't test voice agent behavior cheaply via text
- **Cost**: Realtime API costs $0.06/min even for text testing (30-60x more expensive)

## Goal
Create a unified agent system where both text and voice modes use identical logic, allowing cheap text-based testing of voice agent configurations.

## Architecture Solution

### 1. Shared Agent Configuration Layer
Create a single source of truth for all agent behaviors.

#### File: `backend/agents/agent_config.py`
```python
class UnifiedAgentConfig:
    """Single configuration for all agents across all modes"""
    
    # System instructions (used by both APIs)
    GREETING_INSTRUCTIONS = """
    You are a helpful assistant for Sakura Ramen House.
    [Full instructions here...]
    """
    
    RESERVATION_INSTRUCTIONS = """
    Handle reservations with these rules...
    """
    
    # Shared knowledge base
    RESTAURANT_INFO = {
        "hours": {
            "monday_thursday": "11:30 AM - 9:30 PM",
            "friday_saturday": "11:30 AM - 10:30 PM",
            "sunday": "12:00 PM - 9:00 PM"
        },
        "menu": {
            # Menu items
        },
        "policies": {
            # Restaurant policies
        }
    }
    
    # Intent patterns
    INTENT_PATTERNS = {
        "reservation": ["book", "reserve", "table", "reservation"],
        "menu": ["menu", "food", "ramen", "dish", "order"],
        "hours": ["hours", "open", "close", "when"],
        "location": ["where", "address", "location", "directions"]
    }
    
    # Response templates
    RESPONSE_TEMPLATES = {
        "greeting": "Welcome to Sakura Ramen House! I can help you with...",
        "reservation_unavailable": "We operate on a walk-in basis only...",
        # More templates
    }
```

### 2. Agent Orchestrator
Handles routing and logic for both modes.

#### File: `backend/services/agent_orchestrator.py`
```python
from agents.agent_config import UnifiedAgentConfig

class AgentOrchestrator:
    """Orchestrates agent logic for both text and voice modes"""
    
    def __init__(self):
        self.config = UnifiedAgentConfig()
        self.context = {}
    
    def process_input(self, text: str, mode: str = "text") -> dict:
        """Process input regardless of source"""
        
        # 1. Classify intent
        intent = self.classify_intent(text)
        
        # 2. Route to appropriate handler
        if intent == "reservation":
            response = self.handle_reservation(text)
        elif intent == "menu":
            response = self.handle_menu_query(text)
        elif intent == "hours":
            response = self.handle_hours_query(text)
        else:
            response = self.handle_general(text)
        
        # 3. Format for mode
        if mode == "realtime":
            return self.format_for_realtime(response)
        else:
            return self.format_for_text(response)
    
    def classify_intent(self, text: str) -> str:
        """Classify user intent using shared patterns"""
        text_lower = text.lower()
        
        for intent, patterns in self.config.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return intent
        
        return "general"
    
    def get_instructions_for_mode(self, mode: str) -> str:
        """Get appropriate instructions for API mode"""
        base = self.config.GREETING_INSTRUCTIONS
        
        if mode == "realtime":
            # Add voice-specific instructions
            return base + "\nSpeak naturally and conversationally."
        else:
            # Add text-specific instructions
            return base + "\nProvide clear, concise text responses."
```

### 3. Update Existing Services

#### Update: `backend/services/openai_service.py`
```python
from services.agent_orchestrator import AgentOrchestrator

class OpenAIService:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()
    
    async def process_message(self, text: str) -> tuple:
        # Use orchestrator for logic
        result = self.orchestrator.process_input(text, mode="text")
        
        # If needs vector store, use Assistants API
        if result.get("needs_knowledge"):
            return await self.process_with_assistants(text)
        
        # Otherwise use faster Chat API
        return result["response"], result["state"]
```

#### Update: `backend/realtime_agents/session_manager.py`
```python
from services.agent_orchestrator import AgentOrchestrator

class RestaurantRealtimeSession:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()
    
    async def initialize(self):
        # Use same instructions as text mode
        instructions = self.orchestrator.get_instructions_for_mode("realtime")
        
        # Configure RealtimeAgent with unified config
        self.agent = RealtimeAgent(
            name="SakuraRamenAssistant",
            instructions=instructions,
            tools=[...]
        )
```

#### Update: `backend/websocket_handler.py`
```python
from services.agent_orchestrator import AgentOrchestrator

# Add test mode flag
test_realtime_mode = message.get("test_mode", False)

if test_realtime_mode:
    # Process as if it were realtime but via text
    orchestrator = AgentOrchestrator()
    response = orchestrator.process_input(text, mode="realtime")
else:
    # Normal text processing
    response = orchestrator.process_input(text, mode="text")
```

## Implementation Steps

### Phase 1: Create Configuration Layer
- [ ] Create `backend/agents/agent_config.py`
- [ ] Define all instructions in one place
- [ ] Define intent patterns
- [ ] Define response templates
- [ ] Consolidate restaurant knowledge

### Phase 2: Build Orchestrator
- [ ] Create `backend/services/agent_orchestrator.py`
- [ ] Implement intent classification
- [ ] Implement routing logic
- [ ] Add context management
- [ ] Create response formatting

### Phase 3: Update Text Mode
- [ ] Modify `openai_service.py` to use orchestrator
- [ ] Update `websocket_handler.py` to use orchestrator
- [ ] Add test mode flag for Realtime simulation
- [ ] Ensure backward compatibility

### Phase 4: Update Voice Mode
- [ ] Modify realtime session creation to use config
- [ ] Pass unified instructions to Realtime API
- [ ] Ensure consistent behavior

### Phase 5: Testing Framework
- [ ] Add test mode toggle in frontend
- [ ] Create test scenarios
- [ ] Verify identical responses
- [ ] Performance testing

## Testing Strategy

### Test Mode Usage
1. **Frontend**: Add checkbox "Test Voice Agent via Text"
2. **Backend**: When enabled, WebSocket uses Realtime formatting
3. **Cost**: Uses cheap text API but mimics voice behavior
4. **Validation**: Compare responses between modes

### Test Scenarios
```python
test_inputs = [
    "Hello",
    "What are your hours?",
    "Show me the menu",
    "I want to make a reservation",
    "Do you have vegetarian options?",
]

# Run through both modes
for input in test_inputs:
    text_response = test_via_websocket(input)
    voice_response = test_via_realtime(input)  # Expensive, run sparingly
    assert similar(text_response, voice_response)
```

## Cost Analysis

### Current Costs
- **Text API**: ~$0.001 per message
- **Realtime API**: $0.06 per minute (even for text)
- **Testing 100 messages**:
  - Via text: ~$0.10
  - Via Realtime: ~$3.00 (30x more)

### With Unified System
- Test voice agents via text mode
- Same behavior, 30x cheaper
- Only use Realtime for final voice testing

## Benefits

1. **Single Source of Truth**: One configuration for all agents
2. **Cost Effective**: Test voice behavior at text prices
3. **Maintainable**: Update logic in one place
4. **Consistent**: Same responses across all modes
5. **Testable**: Easy to validate behavior

## Migration Path

### Step 1: Parallel Implementation
- Build new system alongside existing
- No breaking changes

### Step 2: Gradual Migration
- Start with simple intents (greeting, hours)
- Move complex logic gradually

### Step 3: Validation
- A/B test responses
- Ensure no regression

### Step 4: Deprecation
- Remove old agent implementations
- Clean up duplicate code

## Files to Create/Modify

### New Files
1. `backend/agents/agent_config.py` - Unified configuration
2. `backend/services/agent_orchestrator.py` - Shared logic
3. `backend/tests/test_unified_agents.py` - Test suite

### Modified Files
1. `backend/services/openai_service.py` - Use orchestrator
2. `backend/websocket_handler.py` - Add test mode
3. `backend/main.py` - Update Realtime config
4. `frontend/src/components/MessageInput.vue` - Add test mode toggle

## Success Metrics

1. **Functional**: Identical responses between modes
2. **Performance**: <1s response time in text mode
3. **Cost**: 90% reduction in testing costs
4. **Maintenance**: Single configuration file
5. **Testing**: 100% coverage of intents

## Timeline

- **Week 1**: Configuration layer and orchestrator
- **Week 2**: Update existing services
- **Week 3**: Testing and validation
- **Week 4**: Documentation and deployment

## Notes

- Keep existing system running during migration
- Test extensively before switching
- Monitor costs closely
- Document all agent behaviors
- Consider adding analytics to track usage patterns