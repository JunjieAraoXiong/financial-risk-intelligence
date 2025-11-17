# FE-EKG Documentation Index

Complete documentation for the Financial Event Evolution Knowledge Graph (FE-EKG) system.

**Last Updated:** 2025-11-15
**Documentation Version:** 2.0 (Consolidated)

---

## 📚 Core Documentation

### [README.md](README.md)
**Main project documentation** - Overview, quick start, features, and architecture.

**Topics:**
- Project overview and motivation
- Installation and setup instructions
- Core features and capabilities
- Architecture overview
- Usage examples
- Contributing guidelines

**Start here** if you're new to the project.

---

### [PROJECT_GUIDE.md](PROJECT_GUIDE.md)
**Comprehensive project guide** - Detailed instructions for Claude Code and developers.

**Topics:**
- Complete project structure
- Technology stack details
- Development workflow
- Stage-by-stage implementation
- Key files and their purposes
- Common development tasks
- Troubleshooting guide

**Use this** for in-depth development guidance.

---

## 🔧 Setup & Configuration

### [ALLEGROGRAPH_SETUP.md](ALLEGROGRAPH_SETUP.md) (9.4K)
**AllegroGraph integration guide** - Connecting to AllegroGraph via HTTPS.

**Topics:**
- HTTPS connection setup (port 443)
- Why port 10035 doesn't work
- Configuration and environment variables
- Usage examples and scripts
- Permission management
- Alternative solutions (Fuseki, RDFLib)
- Troubleshooting

**Quick answer:** Use HTTPS with explicit port 443 instead of port 10035.

---

### [NEO4J_SETUP.md](NEO4J_SETUP.md) (3.3K)
**Neo4j database setup** - Primary graph database configuration.

**Topics:**
- Docker-based Neo4j setup
- Connection configuration
- Schema creation
- Data loading
- Query examples

---

### [RDF_SETUP.md](RDF_SETUP.md) (19K)
**RDF and ontology management** - Converting data to RDF and managing triple stores.

**Topics:**
- Neo4j to RDF conversion
- RDF database options comparison
- Turtle file generation
- SPARQL query examples
- Triple store selection guide

---

## 📊 Case Studies

### [CASE_STUDY_LEHMAN.md](CASE_STUDY_LEHMAN.md) (15K)
**Lehman Brothers crisis analysis** - Complete pipeline for Lehman case study.

**Topics:**
- Lehman Brothers data processing
- Capital IQ integration
- Event extraction and classification
- Entity resolution
- Risk identification
- Quick start guide
- Pipeline walkthrough

**Real-world case study** demonstrating FE-EKG capabilities.

---

## 🎨 Visualization

### [VISUALIZATIONS.md](VISUALIZATIONS.md) (42K)
**Complete visualization guide** - Static, interactive, and timeline visualizations.

**Topics:**
- Three-layer graph visualization
- Evolution network diagrams
- Risk heatmaps
- Timeline visualizations
- Interactive HTML graphs
- Clean visual design principles
- Color scheme documentation
- D3.js integration

**See:** [results/](../results/) folder for generated visualizations.

---

## 🤖 AI Integration

### [LLM_INTEGRATION.md](LLM_INTEGRATION.md) (51K)
**LLM and NLP features** - AI-powered analysis and classification.

**Topics:**
- NVIDIA NeMo integration
- Semantic analysis
- Event classification improvements
- NLP value addition
- LLM playground guide
- Fine-tuning strategies
- API integration

**Latest features:** GPT-4 and NeMo for semantic enrichment.

---

## ⚡ Performance

### [OPTIMIZATION.md](OPTIMIZATION.md) (52K)
**Performance optimization guide** - Strategies for scaling and efficiency.

**Topics:**
- Performance benchmarks
- Pipeline comparison (v1 vs v2)
- ETL completion analysis
- Database query optimization
- Caching strategies
- Connection pooling
- Bottleneck identification

**Key metrics:** Query performance, data processing speed, visualization rendering.

---

## 📁 Documentation Structure

```
docs/
├── INDEX.md                    # This file
├── README.md                   # Main documentation
├── PROJECT_GUIDE.md            # Developer guide
│
├── Setup & Configuration
│   ├── ALLEGROGRAPH_SETUP.md   # AllegroGraph integration
│   ├── NEO4J_SETUP.md          # Neo4j setup
│   └── RDF_SETUP.md            # RDF and triple stores
│
├── Case Studies
│   └── CASE_STUDY_LEHMAN.md    # Lehman Brothers analysis
│
├── Features
│   ├── VISUALIZATIONS.md       # Visualization system
│   ├── LLM_INTEGRATION.md      # AI/NLP features
│   └── OPTIMIZATION.md         # Performance tuning
│
└── (Additional docs as needed)
```

---

## 🎯 Quick Navigation

### For New Users
1. Start with [README.md](README.md)
2. Follow [NEO4J_SETUP.md](NEO4J_SETUP.md) for database setup
3. Try the Lehman case study: [CASE_STUDY_LEHMAN.md](CASE_STUDY_LEHMAN.md)
4. Explore visualizations: [VISUALIZATIONS.md](VISUALIZATIONS.md)

### For Developers
1. Read [PROJECT_GUIDE.md](PROJECT_GUIDE.md) thoroughly
2. Set up triple stores: [ALLEGROGRAPH_SETUP.md](ALLEGROGRAPH_SETUP.md) or [RDF_SETUP.md](RDF_SETUP.md)
3. Optimize performance: [OPTIMIZATION.md](OPTIMIZATION.md)
4. Integrate AI features: [LLM_INTEGRATION.md](LLM_INTEGRATION.md)

### For Researchers
1. Review case study methodology: [CASE_STUDY_LEHMAN.md](CASE_STUDY_LEHMAN.md)
2. Examine visualization techniques: [VISUALIZATIONS.md](VISUALIZATIONS.md)
3. Explore NLP capabilities: [LLM_INTEGRATION.md](LLM_INTEGRATION.md)
4. Analyze performance metrics: [OPTIMIZATION.md](OPTIMIZATION.md)

---

## 📖 External Resources

### Project Links
- **GitHub:** (Add your repository URL)
- **Paper:** Liu et al. (2024) "Risk identification and management through knowledge Association"
- **Demo:** See `api/demo.html` for interactive demo

### Related Documentation
- **Neo4j Docs:** https://neo4j.com/docs/
- **AllegroGraph Docs:** https://franz.com/agraph/support/documentation/
- **RDFLib:** https://rdflib.readthedocs.io/
- **NVIDIA NeMo:** https://docs.nvidia.com/nemo-framework/

---

## 📝 Documentation Changelog

### Version 2.0 (2025-11-15)
- ✅ Consolidated 25+ markdown files into 9 organized documents
- ✅ Created docs/ folder structure
- ✅ Removed duplicate content
- ✅ Added cross-references and navigation
- ✅ Improved organization by topic

### Version 1.0 (2025-11-10)
- Initial documentation scattered across root directory
- Multiple files covering same topics
- 25+ separate markdown files

---

## 🔍 Finding Information

### Search by Topic

**Database Setup:**
- Neo4j: [NEO4J_SETUP.md](NEO4J_SETUP.md)
- AllegroGraph: [ALLEGROGRAPH_SETUP.md](ALLEGROGRAPH_SETUP.md)
- RDF: [RDF_SETUP.md](RDF_SETUP.md)

**Features:**
- Visualization: [VISUALIZATIONS.md](VISUALIZATIONS.md)
- AI/NLP: [LLM_INTEGRATION.md](LLM_INTEGRATION.md)
- Performance: [OPTIMIZATION.md](OPTIMIZATION.md)

**Examples:**
- Real data: [CASE_STUDY_LEHMAN.md](CASE_STUDY_LEHMAN.md)
- Quick start: [README.md](README.md)
- Development: [PROJECT_GUIDE.md](PROJECT_GUIDE.md)

---

## 💡 Tips

### Documentation Best Practices
1. **Start broad, then deep** - Begin with README, dive into specific guides
2. **Use the index** - This file helps you find what you need quickly
3. **Check examples** - Case studies show real-world usage
4. **Follow links** - Documents cross-reference each other

### Keeping Documentation Updated
- Update relevant docs when adding features
- Keep code examples in sync with actual code
- Add troubleshooting tips as you encounter issues
- Document configuration changes immediately

---

## 📧 Getting Help

### Documentation Issues
- **Missing info?** Open an issue or PR
- **Unclear sections?** Request clarification
- **Found errors?** Submit corrections

### General Support
- Check [PROJECT_GUIDE.md](PROJECT_GUIDE.md) troubleshooting section
- Review relevant setup guides
- Examine case studies for examples

---

**Happy coding! 🚀**

*Generated by Claude Code - Documentation Consolidation v2.0*
