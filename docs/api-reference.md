# AnonSuite API Reference

## Core Module Interface

### AnonymityModule

```python
class AnonymityModule:
    def start(self, config: Dict) -> Result:
        """Start anonymity services"""
        
    def stop(self) -> Result:
        """Stop anonymity services"""
        
    def status(self) -> Status:
        """Get current status"""
        
    def configure(self, settings: Dict) -> Result:
        """Update configuration"""
```

### WiFiModule

```python
class WiFiModule:
    def scan_networks(self, interface: str) -> List[Network]:
        """Scan for available networks"""
        
    def start_attack(self, attack_type: str, target: str) -> Result:
        """Start WiFi attack"""
        
    def stop_attack(self) -> Result:
        """Stop current attack"""
```

## Configuration Schema

### Anonymity Configuration
```json
{
  "tor_instances": 3,
  "load_balancer": "haproxy",
  "exit_nodes": ["us", "de", "nl"],
  "circuit_timeout": 30
}
```

### WiFi Configuration
```json
{
  "interface": "wlan0",
  "attack_modes": ["rogue_ap", "pixie_dust"],
  "capture_path": "/tmp/anonsuite/captures"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| E001 | Configuration error |
| E002 | Network interface error |
| E003 | Permission denied |
| E004 | Service startup failed |
| E005 | Attack failed |

## Command Line Interface

### Main Commands
```bash
anonsuite                    # Interactive menu
anonsuite --help            # Show help
anonsuite --version         # Show version
anonsuite --health-check    # Health check
```

### Environment Variables
- `ANONSUITE_ENV`: Environment (development/production)
- `ANONSUITE_LOG_LEVEL`: Logging level
- `ANONSUITE_CONFIG_PATH`: Configuration directory
