# ADHD Print - Task Printing System

A Django-based task management system with integrated thermal printing capabilities for ESC/POS printers.

## 💡 Inspiration & Methodology

### The Science Behind Thermal Receipt Printing for ADHD

This project was inspired by groundbreaking work demonstrating how thermal receipt printers can effectively combat procrastination and support ADHD management through physical, tangible task reminders.

#### 🔬 Research & Methodology

The approach is based on the principle that **physical objects create stronger psychological commitment** than digital reminders. As detailed in [Laurie Herault's research](https://www.laurieherault.com/articles/a-thermal-receipt-printer-cured-my-procrastination), thermal printing leverages several key psychological mechanisms:

1. **Physical Presence**: Unlike digital notifications that can be dismissed, printed tasks create a persistent physical reminder
2. **Immediate Feedback**: The act of printing provides instant gratification and reinforcement
3. **Tactile Engagement**: Physical handling of task cards creates stronger memory formation
4. **Visual Clarity**: High-contrast thermal printing provides clear, readable task information
5. **Completion Ritual**: Physical destruction/filing of completed tasks provides psychological closure

#### 📚 Inspiring Articles & Research

- **[A Thermal Receipt Printer Cured My Procrastination](https://www.laurieherault.com/articles/a-thermal-receipt-printer-cured-my-procrastination)** - The foundational research that inspired this project
- **[Hacker News Discussion](https://news.ycombinator.com/item?id=44256499)** - Community insights and experiences with thermal printing for productivity
- **[Trying to Stop Procrastination with My Receipt Printer](https://joeldare.com/trying-to-stop-procrastination-with-my-receipt-printer)** - Practical implementation experiences
- **[Can a Thermal Printer Cure ADHD?](https://hackaday.com/2025/08/06/can-a-thermal-printer-cure-adhd/)** - Technical analysis of thermal printing for ADHD management
- **[Colonnes - Digital Minimalism](https://www.colonnes.com/)** - Philosophy of intentional technology use

#### 🛠️ Technical Inspiration

- **[CodingWithLewis/ReceiptPrinterAgent](https://github.com/CodingWithLewis/ReceiptPrinterAgent)** - Python library for receipt printer integration
- **[Receipt Printer Agent Demo](https://www.youtube.com/watch?v=xg45b8UXoZI)** - Video demonstration of thermal printing automation

### Why This Approach Works for ADHD

1. **Reduces Decision Fatigue**: Pre-planned, printed tasks eliminate the need to constantly decide what to do next
2. **Provides Immediate Dopamine**: The printing action itself provides instant gratification
3. **Creates Accountability**: Physical tasks are harder to ignore than digital ones
4. **Supports Executive Function**: External structure compensates for internal organizational challenges
5. **Enables Hyperfocus**: Clear, single-task focus reduces overwhelming choice paralysis

### Implementation Philosophy

This system combines the proven effectiveness of thermal printing with modern web technology to create a comprehensive ADHD management tool that:

- **Bridges Digital and Physical**: Web-based task creation with physical output
- **Supports Routine Building**: Automated periodic tasks for habit formation
- **Reduces Cognitive Load**: Simple, clear interface with minimal distractions
- **Provides Flexibility**: Multiple urgency levels and hierarchical organization
- **Ensures Reliability**: Background automation and robust error handling

---

## ✨ Features

- **Hierarchical Task Management**: Organize tasks with up to 3 levels of nesting
- **Periodic/Repeating Tasks**: Set up daily, weekly, monthly, or yearly recurring tasks
- **Task Urgency Levels**: Critical, Urgent, Normal, and Low priority levels
- **Due Date Tracking**: Optional due dates with overdue indicators
- **Task Completion**: Mark tasks as done with status tracking
- **Thermal Printing**: Print tasks directly to ESC/POS thermal printers (tested with Qian QOP-T80UL-RI-02)
- **Print Modal**: Automatic "Print this task?" prompt after creating tasks
- **Material Design Icons**: Visual urgency indicators in printouts
- **Professional Layout**: High-quality thermal printer output with borders and proper typography
- **Configurable Database**: Flexible database location and settings via environment variables
- **Background Jobs**: Integrated automated maintenance system (no cron setup required)
- **ASGI Support**: Modern asynchronous deployment for better performance
- **Multiple Deployment Options**: Docker, LXC containers, traditional servers, and ASGI

---

## Requirements

- Python 3.8+
- Django 5.2.7
- Pillow (PIL) for image processing
- ESC/POS thermal printer (tested with Qian QOP-T80UL-RI-02)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd adhd-print
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser (optional):
```bash
python manage.py createsuperuser
```

6. Configure settings (optional):
   
   Copy the example environment file and customize:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
   
   Available environment variables:
   - `ADHD_PRINT_DATA_DIR`: Data directory path (default: `./data`)
   - `ADHD_PRINT_DB_NAME`: Database filename (default: `adhd_print.db`)
   - `ADHD_PRINT_PRINTER_HOST`: Printer IP address (default: `192.168.1.40`)
   - `ADHD_PRINT_PRINTER_PORT`: Printer port (default: `9100`)
   - `ADHD_PRINT_USE_GRAPHICS`: Enable graphics printing (default: `True`)

7. Configure printer settings in `adhd_print_project/settings.py` or via environment variables:
```python
PRINTER_HOST = '192.168.1.40'  # Your printer IP
PRINTER_PORT = 9100
PRINTER_USE_GRAPHICS = True
```

## Usage

## 🚀 Deployment Options

This application supports multiple deployment methods. For complete deployment instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

### Quick Development Setup

```bash
# Basic setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Production Deployment Options

- **🐳 [Docker Deployment](DEPLOYMENT.md#docker-deployment)** - Complete containerization with nginx, PostgreSQL, Redis
- **⚡ [ASGI Production](DEPLOYMENT.md#asgi-production-deployment)** - Modern async deployment with uvicorn/gunicorn  
- **📦 [Proxmox LXC](DEPLOYMENT.md#proxmox-lxc-container-deployment)** - Lightweight Alpine Linux containers with autostart
- **🖥️ [Traditional Server](DEPLOYMENT.md#traditional-server-deployment)** - Standard server deployment with nginx/supervisor

Each deployment method includes complete instructions, configuration examples, and troubleshooting guidance.

The application includes an integrated background job system that automatically handles periodic task maintenance every night at 2:00 AM. No additional cron job setup is required. For complete feature documentation including periodic tasks and background jobs, see **[FEATURES.md](FEATURES.md)**.

2. Access the application at http://127.0.0.1:8000/tasks/

3. Create tasks and organize them hierarchically

4. Use the print button to print tasks with confirmation modal

## 📚 Documentation

### Quick Links
- **[🚀 Complete Deployment Guide](DEPLOYMENT.md)** - All deployment options (Docker, ASGI, LXC, traditional)
- **[🎯 Features Guide](FEATURES.md)** - Complete feature overview including periodic tasks and background jobs  
- **[🧪 Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing documentation and recent fixes
- **[⚡ ASGI Setup](ASGI_SETUP.md)** - Modern ASGI deployment for production

### Project Structure

```
adhd-print/
├── .env.example               # Environment configuration template
├── .env.asgi.example         # ASGI configuration template
├── README.md                  # This file - project overview
├── DEPLOYMENT.md              # 🚀 Complete deployment guide
├── FEATURES.md                # 🎯 Complete features documentation
├── TESTING_GUIDE.md           # 🧪 Comprehensive testing guide
├── ASGI_SETUP.md             # ⚡ ASGI deployment guide
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management
├── start_asgi.sh             # ASGI server startup script
├── data/                      # 📁 Data directory (databases, user files)
│   └── adhd_print.db         # SQLite database (default location)
├── adhd_print_project/       # Django project settings
├── tasks/                    # Main tasks application
├── static/                   # Static assets (fonts, icons)
├── scripts/                  # 📁 Utility scripts
├── deployment/               # 📁 Deployment configurations
│   └── lxc/                 # Proxmox LXC container setup
└── venv/                    # Virtual environment
```

## 🖨️ Printing Features

For complete printing system documentation, see **[FEATURES.md](FEATURES.md#advanced-printing-system)**.

### Quick Printer Setup

Configure your thermal printer settings:

```bash
export ADHD_PRINT_PRINTER_HOST=192.168.1.100
export ADHD_PRINT_PRINTER_PORT=9100
export ADHD_PRINT_USE_GRAPHICS=True
```

### Print Modes

- **Graphics Mode**: High-quality bitmap printing with Material Design icons and Roboto fonts
- **Text Mode**: ASCII fallback for basic printers with automatic fallback
- **Professional Layout**: Bordered output with task hierarchy and urgency indicators

### Tested Hardware
- **Qian QOP-T80UL-RI-02** (Primary tested model)
- **ESC/POS Protocol**: Compatible with most thermal receipt printers
- **Network Printing**: TCP/IP connection support

## Configuration

### Database Configuration

The database location and name are configurable via environment variables:

```bash
# Default: ./data/adhd_print.db
export ADHD_PRINT_DATA_DIR=/custom/path/to/data
export ADHD_PRINT_DB_NAME=my_tasks.db
```

### Printer Configuration

Configure your thermal printer settings:

```bash
export ADHD_PRINT_PRINTER_HOST=192.168.1.100
export ADHD_PRINT_PRINTER_PORT=9100
export ADHD_PRINT_USE_GRAPHICS=True
```

### Environment File

For persistent configuration, copy `.env.example` to `.env`:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## 🧪 Testing

The application includes a comprehensive test suite. For complete testing documentation, see **[TESTING_GUIDE.md](TESTING_GUIDE.md)**.

### Quick Test Commands

```bash
# Run all tests
python manage.py test

# Run with optimized settings
python manage.py test --settings=adhd_print_project.test_settings

# Run with coverage
./run_tests.sh coverage

# Generate HTML coverage report
./run_tests.sh html
```

### Test Coverage
- **24+ Comprehensive Tests**: Core functionality and recent bug fixes
- **100% Passing Rate**: All tests consistently pass
- **Multiple Categories**: Model, view, integration, JavaScript, and background job tests
- **Recent Fixes Validation**: All recent improvements thoroughly tested

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]