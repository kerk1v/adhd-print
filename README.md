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

## 📚 Quick and dirty instructions: 

### 🎯 User Manual: Getting Started with ADHD Print

This comprehensive user guide will help you effectively use the ADHD Print Task Management System for maximum productivity and ADHD support.

#### **Initial Setup & Access**

1. **First Login**
   - Navigate to `http://localhost:8000/tasks/` (or your server address)
   - Click "Login" and use your admin credentials
   - If no user exists, create one: `python manage.py createsuperuser`

2. **Dashboard Overview**
   - **Task List**: Main view showing all your tasks organized hierarchically
   - **Today's Tasks**: Convenient menu item showing only tasks due today or overdue
   - **Add Task Button**: Green "+" button to create new tasks
   - **Filter Options**: Sort by urgency, due date, or completion status
   - **Print Controls**: Individual print buttons for each task

#### **Creating Tasks Effectively**

1. **Basic Task Creation**
   - Click the green "Add Task" button
   - **Title**: Keep it concise but specific (e.g., "Review quarterly budget")
   - **Description**: Add context, steps, or notes (optional but recommended)
   - **Parent Task**: Select to create subtasks under existing tasks
   - **Due Date**: Set realistic deadlines (optional)
   - **Urgency Level**: 
     - 🔴 **Critical**: Must be done today, blocks other work
     - 🟠 **Urgent**: Important deadline, high priority
     - 🟡 **Normal**: Standard priority, regular workflow
     - 🟢 **Low**: Nice-to-have, flexible timing

2. **Hierarchical Organization (Up to 3 Levels)**
   ```
   📋 Project: Website Redesign
   ├── 📝 Research competitor websites
   │   ├── ✓ Analyze 5 competitor sites
   │   └── 📝 Document design patterns
   ├── 📝 Create wireframes
   └── 📝 Develop prototype
   ```

3. **Task Hierarchy Best Practices**
   - **Level 1**: Major projects or life areas
   - **Level 2**: Specific deliverables or phases
   - **Level 3**: Actionable steps or subtasks
   - Keep subtasks small and achievable (15-30 minutes each)

#### **Using Periodic/Recurring Tasks**

1. **Setting Up Recurring Tasks**
   - Check "Make this a periodic task" when creating
   - **Frequency Options**:
     - **Daily**: Every day (e.g., "Take medication", "Review calendar")
     - **Weekly**: Every week (e.g., "Grocery shopping", "Laundry")
     - **Monthly**: Every month (e.g., "Pay bills", "Budget review")
     - **Yearly**: Every year (e.g., "File taxes", "Annual checkup")

2. **Periodic Task Examples**
   ```
   Daily Tasks:
   - Take morning medication
   - Review today's priorities
   - 10-minute desk cleanup
   
   Weekly Tasks:
   - Grocery shopping
   - Laundry and clothing prep
   - Weekly planning session
   
   Monthly Tasks:
   - Budget review and banking
   - Deep clean living space
   - Medication refill check
   ```

#### **Printing Tasks for Maximum ADHD Benefit**

1. **When to Print Tasks**
   - **Start of Day**: Print today's critical and urgent tasks
   - **After Creating Tasks**: Use the auto-prompt to print immediately
   - **Project Focus**: Print all subtasks for a specific project
   - **Overwhelm Prevention**: Print just 3-5 tasks to avoid choice paralysis

2. **Print Modal Workflow**
   - After creating a task, you'll see "Print this task?" prompt
   - **"Yes, Print Now"**: Immediately prints the task
   - **"Not Right Now"**: Dismisses modal, can print later
   - **Always Print Button**: Available next to each task

3. **Physical Task Management**
   ```
   Printed Task Workflow:
   1. Print task → Place in visible location
   2. Start working → Move to "doing" area
   3. Complete task → Physical satisfaction of crumpling/filing
   4. Mark complete in system → Digital tracking
   ```

#### **Task Management Strategies for ADHD**

1. **Daily Focus with "Today's Tasks"**
   - Use "Today's Tasks" menu item for daily planning
   - Shows only tasks due today or overdue - perfect for ADHD focus
   - **Morning Routine**: Start day by reviewing Today's Tasks
   - **Overwhelm Prevention**: Filters out future tasks to reduce cognitive load
   - **Priority Clarity**: Immediately see what needs attention today
   - **Print Today's Tasks**: Print the filtered list for physical focus

2. **The "Rule of 3" Method**
   - Print only 3 tasks at a time
   - Complete all 3 before printing more
   - Prevents overwhelming choice paralysis

3. **Urgency-Based Printing**
   - **Morning**: Print all Critical tasks
   - **Midday**: Print Urgent tasks if Critical are done
   - **Afternoon**: Print Normal tasks for momentum
   - **Never**: Print Low tasks unless everything else is done

4. **Project Momentum Technique**
   - Choose one project/parent task
   - Print all its subtasks at once
   - Focus on completing the entire project
   - Provides sense of major accomplishment

5. **Time-Boxing with Physical Tasks**
   - Print task → Set timer for estimated duration
   - Work until timer ends
   - If incomplete, assess: continue or break into smaller tasks
   - Physical task serves as focus anchor

#### **Completion and Progress Tracking**

1. **Marking Tasks Complete**
   - Click the checkmark ✓ next to completed tasks
   - Task will move to completed section
   - Completion percentage shows in parent tasks
   - Use physical destruction of printed task for psychological closure

2. **Progress Monitoring**
   - Parent tasks show completion percentage
   - Due date tracking with overdue indicators
   - Filter view by completion status
   - Review completed tasks for motivation

#### **Advanced Features**

1. **Task Filtering and Views**
   - **All Tasks**: Complete overview
   - **Incomplete Only**: Focus on remaining work
   - **Overdue**: Priority attention needed
   - **By Urgency**: Organized by priority level

2. **Bulk Operations**
   - Print multiple tasks by urgency level
   - Mass completion for related tasks
   - Batch due date updates

#### **ADHD-Specific Tips**

1. **Combating Executive Dysfunction**
   - **Break Large Tasks**: Use 3-level hierarchy to break overwhelming tasks
   - **Start Small**: Print easiest task first for momentum
   - **Physical Anchoring**: Keep printed tasks in consistent location
   - **Routine Building**: Use daily periodic tasks for structure

2. **Managing Hyperfocus**
   - **Project Mode**: Print all subtasks for deep work sessions
   - **Time Boundaries**: Set alarms even with printed tasks
   - **Progress Visibility**: Check off subtasks to see progress during hyperfocus

3. **Preventing Overwhelm**
   - **Limited Printing**: Never print more than 5 tasks at once
   - **Priority First**: Always handle Critical/Urgent before Normal/Low
   - **Physical Limits**: Use physical space to limit concurrent tasks

4. **Building Dopamine Loops**
   - **Immediate Printing**: Use auto-print modal for instant gratification
   - **Physical Completion**: Enjoy crumpling completed task printouts
   - **Visual Progress**: Watch parent task percentages increase
   - **Small Wins**: Celebrate each checkmark and completion

#### **Troubleshooting Common Issues**

1. **Printer Not Working**
   - Check printer IP address in settings
   - Verify network connection
   - Try text mode if graphics mode fails
   - See [FEATURES.md](FEATURES.md) for detailed printer troubleshooting

2. **Task Organization Confusion**
   - Start with flat task list, add hierarchy gradually
   - Use descriptive task titles
   - Limit hierarchy to 2 levels initially

3. **Overwhelm from Too Many Tasks**
   - Use urgency levels strictly
   - Print only Critical tasks until comfortable
   - Archive or delete old completed tasks
   - Focus on daily periodic tasks for routine

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