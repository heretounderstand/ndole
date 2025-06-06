# Educational AI Platform

An open-source educational AI platform that combines document management with AI-powered learning tools, designed for cost-effective education in resource-constrained environments.

## Overview

This platform allows users to create document repositories, leverage RAG (Retrieval-Augmented Generation) systems, and generate interactive learning content. Built with accessibility and cost-effectiveness in mind, it serves students and educators who need powerful learning tools without breaking the bank.

## Features

### Core Functionality
- **Document Repository Management**: Create, organize, and share educational document collections
- **RAG-Powered Learning**: Select document repositories to feed into a Retrieval-Augmented Generation system
- **AI Course Generation**: Automatically generate structured courses from selected documents
- **Interactive Quizzes**: Create quizzes and assessments based on document content
- **Mathematical Operations**: Custom SQL-like query language for sympy integration

### Key Benefits
- Cost-effective solution for educational institutions
- Open-source and community-driven development
- Designed for resource-constrained environments
- Personalized and interactive learning experience

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Supabase (PostgreSQL with real-time capabilities)
- **Embeddings**: all-MiniLM-L6-v2 (lightweight and efficient)
- **LLM**: Google Gemini
- **Custom Feature**: Sympy Query Language (SQL-style mathematical operations)

## Installation

```bash
# Clone the repository
git clone https://github.com/heretounderstand/ndole.git
cd ndole

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.streamlit/secrets.toml` file with the following configuration:

```toml
[supabase]
url = "your_supabase_url"
api_key = "your_supabase_api_key"

[gemini]
api_key = "your_gemini_api_key"
```

## Usage

### Starting the Application

```bash
streamlit run home.py
```

### Basic Workflow

1. **Create Repository**: Upload and organize your educational documents
2. **Configure RAG System**: Select which repositories to include in your knowledge base
3. **Generate Content**: Use AI to create courses and quizzes from your documents
4. **Mathematical Queries**: Use the custom Sympy Query Language for mathematical operations

### Sympy Query Language Examples

#### 1. Define symbols and variables
```sql
let x                     -- define a symbol
let y = 5                 -- define a variable with value
let f = x**2              -- define an expression
```

#### 2. Mathematical operations
```sql
solve(x**2 - 4, x)                    -- solve equation for x
expand((x+1)**2)                      -- expand expression
factor(x**2 + 2*x + 1)                -- factor expression
simplify(sin(x)**2 + cos(x)**2)       -- simplify expression
diff(x**2, x)                         -- differentiate
integrate(x**2, x)                    -- integrate
limit(sin(x)/x, x, 0)                 -- find limit
subs(x**2, x, 2)                      -- substitute x=2
```

#### 3. LaTeX input support
```sql
latex x^2 + 2x + 1                   -- parse LaTeX expression
```

#### 4. Direct expressions
```sql
x**2 + 2*x + 1                       -- evaluate expression
```

#### 5. Chaining operations
```sql
expand((x+1)**2) | factor($)         -- chain operations with pipe
x**2 + 2*x + 1 | factor($)           -- use result in next operation
x**2 + 2*x + 1 | let result          -- store result in variable
```

#### 6. Using last result
```sql
$                                     -- reference last result
factor($)                             -- use last result as input
diff($, x)                            -- use last result as first argument
```

## Contributing

We welcome contributions from the community! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** and add tests if applicable
4. **Commit your changes**: `git commit -m 'Add feature description'`
5. **Push to your fork**: `git push origin feature-name`
6. **Submit a pull request**

### Areas for Contribution

- UI/UX improvements
- Additional LLM integrations
- Performance optimizations
- Documentation enhancements
- Testing and bug fixes

## Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Offline mode capabilities
- [ ] Advanced mathematical visualization
- [ ] Integration with popular LMS platforms

## License

This project is currently unlicensed. A license will be added soon to clarify usage terms.

## Support

If you encounter any issues or have questions, please contact me directly:

- Email: kadrilud@gmail.com
- LinkedIn: [Your LinkedIn Profile](https://linkedin.com/in/adrien-kadji-bb1720279)
- Create an [Adrien KADJI](https://github.com/heretounderstand/ndole/issues) on GitHub

## Acknowledgments

- Built as a final year project at [ENSPM]
- Inspired by the need for accessible educational technology in Cameroon
- Thanks to the open-source community for the amazing tools and libraries

## Author

**Adrien KADJI** - Data Science Engineering Student  
Email: kadrilud@gmail.com  
LinkedIn: [Adrien KADJI](https://linkedin.com/in/adrien-kadji-bb1720279)

---

*Built with ❤️ for accessible education*
