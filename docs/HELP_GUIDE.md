# A2 Intelligence - Help Guide
## Troubleshooting & FAQs

---

## Table of Contents

1. [Quick Start Checklist](#quick-start-checklist)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Feature-Specific Help](#feature-specific-help)
4. [Data & Calculations](#data--calculations)
5. [API Reference](#api-reference)
6. [Keyboard Shortcuts](#keyboard-shortcuts)
7. [Browser Compatibility](#browser-compatibility)
8. [Contact Support](#contact-support)

---

## Quick Start Checklist

Before using the platform, ensure you have:

- [ ] Valid login credentials (email/password or Google account)
- [ ] Modern web browser (Chrome, Firefox, Safari, Edge)
- [ ] Stable internet connection
- [ ] At least one portfolio created or sample data access

---

## Common Issues & Solutions

### Login Issues

**Problem: Can't log in with email/password**
- Solution: Check that your email and password are correct
- Try the "Forgot Password" link if available
- Clear browser cache and cookies
- Try a different browser

**Problem: Google Sign-In not working**
- Solution: Ensure pop-ups are not blocked
- Check that third-party cookies are enabled
- Try signing out of Google and signing back in

### Data Loading Issues

**Problem: Dashboard shows "Loading..." indefinitely**
- Solution: Refresh the page (F5 or Ctrl+R)
- Check your internet connection
- Clear browser cache
- Try a hard refresh (Ctrl+Shift+R)

**Problem: Charts not displaying**
- Solution: Ensure JavaScript is enabled
- Check for browser extensions that might block scripts
- Try a different browser

### Export Issues

**Problem: Export button not responding**
- Solution: Wait for data to fully load before exporting
- Check that a portfolio/module is selected
- Try a smaller data set first

**Problem: Downloaded file is empty or corrupted**
- Solution: Check your download folder for the file
- Ensure you have sufficient disk space
- Try a different export format (PDF vs Excel)

### Map Issues

**Problem: Water Risk Map not loading**
- Solution: Check internet connection (maps require online access)
- Ensure WebGL is enabled in your browser
- Try zooming out and refreshing

**Problem: Map markers not showing**
- Solution: Wait for the map to fully load
- Check that filter options aren't hiding all markers
- Reset view using the reset button

---

## Feature-Specific Help

### Carbon Credits Module

**Q: How do I calculate credits for my project?**
1. Go to Carbon Credits > Calculator tab
2. Select your sector (Energy, Forestry, etc.)
3. Choose the appropriate methodology
4. Fill in the required parameters
5. Click "Calculate" to get results
6. Use "Save as Project" to store calculations

**Q: What methodologies are supported?**
The platform supports 40+ certified methodologies from:
- CDM (Clean Development Mechanism)
- VCS (Verified Carbon Standard)
- Gold Standard
- CAR (Climate Action Reserve)
- ACR (American Carbon Registry)
- GCC (Global Carbon Council)

### Nature Risk Module

**Q: How do I complete a LEAP assessment?**
1. Navigate to Nature Risk > LEAP tab
2. **Step 1 - Locate**: Enter entity name, sector, and site information
3. **Step 2 - Evaluate**: Select ecosystem dependencies
4. **Step 3 - Assess**: Choose scenarios and set risk exposure
5. **Step 4 - Prepare**: Document mitigation strategies
6. Click "Submit Assessment" to finalize

**Q: What do the Water Risk colors mean?**
| Color | Risk Level | Water Stress Score |
|-------|------------|-------------------|
| Green | Low | 0-20% |
| Yellow | Medium | 20-40% |
| Orange | High | 40-80% |
| Red | Critical | 80-100% |

**Q: How is GBF alignment calculated?**
GBF alignment is assessed against 23 Global Biodiversity Framework targets:
- **Aligned**: Full compliance with target requirements
- **Partial**: Some criteria met, improvements needed
- **Not Aligned**: Significant gaps in compliance

### Stranded Assets Module

**Q: How do I assess reserve impairment?**
1. Go to Stranded Assets > Reserves tab
2. Select reserves from your portfolio
3. Choose a scenario (IEA NZE, APS, STEPS)
4. Set target years (2030-2050)
5. Adjust discount rate if needed
6. Click "Calculate Impairment"

**Q: What scenarios are available?**
- **IEA NZE**: Net Zero Emissions by 2050
- **IEA APS**: Announced Pledges Scenario
- **IEA STEPS**: Stated Policies Scenario

### RE Valuation Module

**Q: Which valuation approach should I use?**
| Approach | Best For |
|----------|----------|
| Direct Cap | Stabilized income properties |
| DCF | Properties with changing cash flows |
| Cost | Unique or new properties |
| Sales Comp | Properties with good comparable sales data |

**Q: How is DCF calculated?**
The DCF approach uses:
- 10-year projection period
- Annual cash flow estimates (NOI)
- Terminal value calculation
- Discount rate (typically 8-12%)
- NPV of all cash flows

### Sustainability Module

**Q: What's the difference between GRESB and LEED?**
| Feature | GRESB | LEED |
|---------|-------|------|
| Level | Portfolio | Property |
| Rating | 1-5 Stars | Certified/Silver/Gold/Platinum |
| Focus | ESG Performance | Green Building |
| Frequency | Annual | One-time (with recertification) |

**Q: How is value premium calculated?**
Value premiums are based on research from:
- Academic studies (Eichholtz, Fuerst & McAllister)
- Industry reports (JLL, CBRE, RICS)
- Regional and sector adjustments applied

### Scenario Analysis Module

**Q: What do the Tornado chart colors mean?**
- **Green bars**: Positive impact on value
- **Red bars**: Negative impact on value
- **Length**: Magnitude of sensitivity

**Q: How do cascading effects work?**
In What-If Analysis, cascading effects model real-world interdependencies:
- Higher vacancy → Increased collection loss
- Lower rent growth → Reduced NOI
- Higher expenses → Lower net income

### Portfolio Analytics Module

**Q: How do I create a scheduled report?**
1. Go to Portfolio Analytics > Scheduled tab
2. Click "New Schedule"
3. Enter report name
4. Select module and format
5. Choose frequency
6. Click "Create"

**Q: What report types are available?**
- Valuation Report
- Climate Risk Report
- Sustainability Report
- TCFD Report
- Investor Report
- Executive Summary

---

## Data & Calculations

### Data Sources

The platform integrates data from:
- IIASA (International Institute for Applied Systems Analysis)
- 20+ climate data sources
- 24 NGFS scenarios
- CBAM regulatory data
- ENCORE database (18 sectors, 60+ ecosystem dependencies)
- GBF targets (23 targets)

### Calculation Methodologies

**Risk Scores**: 0-1 scale converted to categories:
- Low: 0-0.25
- Medium: 0.25-0.5
- High: 0.5-0.75
- Critical: 0.75-1.0

**NPV Calculations**: Use standard discounting:
```
NPV = Σ (Cash Flow_t / (1 + r)^t)
```

**Value Premiums**: Based on certification level:
- Rent premium: 2-20% depending on certification
- Value premium: 1.7x rent premium (cap rate compression)

---

## API Reference

### Key Endpoints

| Module | Endpoint | Method |
|--------|----------|--------|
| Health Check | `/api/health` | GET |
| Carbon Dashboard | `/api/v1/carbon/dashboard` | GET |
| Nature Risk | `/api/v1/nature-risk/dashboard/summary` | GET |
| LEAP Calculate | `/api/v1/nature-risk/leap/calculate` | POST |
| Water Risk | `/api/v1/nature-risk/water-risk/analyze` | POST |
| Stranded Assets | `/api/v1/stranded-assets/dashboard` | GET |
| RE Valuation | `/api/v1/valuation/dashboard` | GET |
| Sustainability | `/api/v1/sustainability/dashboard` | GET |
| Scenarios | `/api/v1/scenarios/dashboard` | GET |
| Portfolio Analytics | `/api/v1/portfolio-analytics/portfolios` | GET |
| Scheduled Reports | `/api/v1/scheduled-reports` | GET/POST |
| Exports | `/api/v1/exports/{module}` | GET/POST |

### Authentication

All API requests require authentication via:
- JWT Bearer Token (for email login)
- Google OAuth Token (for Google login)

Header format:
```
Authorization: Bearer <token>
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Navigate between fields |
| `Enter` | Submit forms |
| `Esc` | Close modals/dialogs |
| `Ctrl+F` | Search (browser) |
| `Ctrl+P` | Print current page |

---

## Browser Compatibility

### Supported Browsers

| Browser | Minimum Version | Status |
|---------|-----------------|--------|
| Chrome | 90+ | Fully Supported |
| Firefox | 88+ | Fully Supported |
| Safari | 14+ | Fully Supported |
| Edge | 90+ | Fully Supported |

### Required Features

- JavaScript enabled
- Cookies enabled
- WebGL enabled (for maps)
- Pop-ups allowed (for Google Sign-In)

### Recommended Settings

- Screen resolution: 1920x1080 or higher
- Enable hardware acceleration
- Disable ad blockers for best experience

---

## Known Limitations

### Data Notes

1. **Stranded Asset Calculator**: Uses sample/reference data for demonstration. Real calculations are performed on this sample data.

2. **Real Estate Valuation Engine**: Uses reference data for construction costs and cap rates. This is appropriate for static reference data.

3. **Some API calls**: May fall back to demo results if external services are unavailable.

### Current Limitations

- Maximum 100 properties per portfolio analysis
- Export files limited to 50MB
- Map displays up to 1000 markers
- Scheduled reports run during off-peak hours

---

## Contact Support

### Getting Help

1. **In-App Help**: Click the help icon (?) in any module
2. **Documentation**: Access this guide and the User Guide
3. **Email Support**: Contact AA Impact Inc. support team

### Reporting Issues

When reporting an issue, please include:
- Browser and version
- Steps to reproduce
- Screenshots if applicable
- Error messages (if any)

### Feature Requests

Submit feature requests through:
- In-app feedback form
- Email to product team

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 2026 | Initial release with all core modules |

---

*A2 Intelligence by AA Impact Inc.*
*Help Guide v1.0 - February 2026*
