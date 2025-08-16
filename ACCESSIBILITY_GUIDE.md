# AnonSuite Accessibility Guide

**Making cybersecurity tools accessible to everyone, regardless of technical background or resources.**

## 🎯 Quick Start for Everyone

### "I'm new to this - what is AnonSuite?"
AnonSuite is a security tool that helps protect your privacy online and test network security. Think of it like a Swiss Army knife for digital privacy and security testing.

### "I don't have much technical knowledge - can I still use this?"
**Yes!** We've designed AnonSuite to be accessible. Here's how to get started:

1. **Try the demo first**: `python -m src.anonsuite --demo`
2. **Use the auto-installer**: Option 5 in the demo mode
3. **Follow the step-by-step wizard**: `python -m src.anonsuite --config-wizard`

## 🚀 Getting Started (Easy Mode)

### Step 1: Basic Check
```bash
python -m src.anonsuite --health-check
```
This tells you what's working and what's missing.

### Step 2: Demo Mode
```bash
python -m src.anonsuite --demo
```
Explore the tool safely without needing to install anything.

### Step 3: Auto-Install Helper
In demo mode, choose option 5 to automatically install missing tools.

## 💡 For Users with Limited Resources

### "I don't have admin/sudo access"
- You can still use the demo mode and configuration wizard
- The tool works in "lite mode" with reduced functionality
- Consider using a virtual machine if possible

### "I can't install additional software"
- The demo mode works with just Python
- Configuration wizard provides learning value
- Use `--explain` commands to learn security concepts

### "I'm on a shared/restricted computer"
- Run from a portable Python installation
- Use temporary directories for data
- All configuration is stored in user directories

## 🛠 Installation Help by Platform

### Linux (Ubuntu/Debian)
```bash
# Copy and paste this one line:
sudo apt update && sudo apt install tor privoxy wireless-tools aircrack-ng
```

### macOS
```bash
# If you have Homebrew:
brew install tor privoxy

# If you don't have Homebrew, install it first:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Windows
- Use WSL (Windows Subsystem for Linux) and follow Linux instructions
- Or use a virtual machine with Linux

## 📚 Educational Features

### Learn Security Concepts
```bash
python -m src.anonsuite --explain tor
python -m src.anonsuite --explain wifi
python -m src.anonsuite --explain anonymity
```

### Interactive Tutorial
```bash
python -m src.anonsuite --tutorial
```

## 🔧 Troubleshooting Common Issues

### "ConfigManager not available" warning
- This is normal - the tool uses a fallback system
- You can still use most features
- Run the configuration wizard to set up properly

### "Missing required tools" errors
- Use the auto-installer in demo mode (option 5)
- Or follow the platform-specific installation commands above
- The tool will work with limited functionality even without all tools

### "Permission denied" errors
- Some features need administrator privileges
- Try the lite mode features first
- Use `sudo` only when specifically requested

### "Network connectivity failed"
- Check your internet connection
- Some features work offline
- WiFi scanning works without internet

## 🎯 Feature Accessibility Matrix

| Feature | Works Without Dependencies | Needs Admin | Educational Value |
|---------|---------------------------|-------------|-------------------|
| Demo Mode | ✅ Yes | ❌ No | ⭐⭐⭐ High |
| Configuration Wizard | ✅ Yes | ❌ No | ⭐⭐ Medium |
| Health Check | ✅ Yes | ❌ No | ⭐⭐ Medium |
| Help System | ✅ Yes | ❌ No | ⭐⭐⭐ High |
| Concept Explanations | ✅ Yes | ❌ No | ⭐⭐⭐ High |
| Auto-Installer | ❌ Depends | ✅ Yes | ⭐ Low |
| Tor Anonymity | ❌ No | ✅ Yes | ⭐⭐ Medium |
| WiFi Scanning | ❌ No | ✅ Yes | ⭐⭐ Medium |

## 🤝 Community Support

### Getting Help
- **Documentation**: Check `docs/` folder for detailed guides
- **Issues**: Report problems on GitHub
- **Questions**: Use GitHub Discussions for help

### Contributing Back
- **Documentation**: Help improve this guide
- **Translation**: Translate guides to other languages
- **Testing**: Test on different systems and report issues
- **Accessibility**: Suggest improvements for better accessibility

## 🔒 Important Notes

### Legal and Ethical Use
- **Always get permission** before testing networks
- **Use only on networks you own** or have explicit authorization
- **Follow local laws** and regulations
- **This tool is for learning** and authorized testing only

### Privacy Considerations
- Configuration files are stored in your user directory
- No personal data is collected or transmitted
- Logs are stored locally only

## 📞 Need More Help?

### If you're stuck:
1. Try the demo mode first: `python -m src.anonsuite --demo`
2. Read the error messages carefully - they usually tell you what to do
3. Check the troubleshooting section above
4. Ask for help on GitHub Discussions

### Remember:
- It's okay to not understand everything at first
- The demo mode is safe to explore
- Every expert was once a beginner
- The tool is designed to teach while you use it

---

**AnonSuite is committed to making cybersecurity accessible to everyone. If you have suggestions for improving accessibility, please let us know!**