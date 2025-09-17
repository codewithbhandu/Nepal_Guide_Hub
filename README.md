# Nepal Guide Hub

**Your Gateway to Authentic Nepal Experiences**

Nepal Guide Hub is a comprehensive tourism platform that connects travelers with verified travel agencies and professional guides in Nepal. Built with Django and featuring a modern green-themed UI, this platform facilitates authentic Nepal tourism experiences through a trusted marketplace.

## 🏔️ Features

### **Three-Actor System**
- **Tourists**: Browse packages, find guides, book experiences, leave reviews
- **Agencies**: Manage guides, create packages, handle bookings, build reputation  
- **Admins**: Verify agencies, oversee platform operations

### **Core Functionality**
- **Agency Verification**: Only verified agencies can offer services
- **Comprehensive Search**: Filter by package type, difficulty, price, location
- **Booking System**: Complete booking workflow with status tracking
- **Rating & Reviews**: Multi-entity rating system for guides, agencies, and packages
- **Guide Management**: Agencies can manage multiple guides with specialties
- **Package Creation**: Rich package details with itineraries and pricing
- **User Profiles**: Detailed profiles for tourists and agencies

### **Modern UI Design**
- **Green Theme**: Beautiful Nepal-inspired color scheme
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Landing Page**: Mode selection interface for users
- **Intuitive Navigation**: User-type specific navigation and dashboards

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL
- Node.js (for TailwindCSS, optional)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd nepal_guide_hub
```

2. **Install dependencies**
```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

3. **Environment Setup**
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=nepal_guide_hub
DB_USER=your-db-username
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

4. **Database Setup**
```bash
# Create database
createdb nepal_guide_hub

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

5. **Run Development Server**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the landing page.

## 📁 Project Structure

```
nepal_guide_hub/
├── apps/
│   ├── accounts/          # User management (Tourist, Agency, Admin)
│   ├── agencies/          # Agency dashboard and management
│   ├── bookings/          # Booking system and ratings
│   ├── core/              # Homepage, search, contact
│   ├── guides/            # Guide profiles and management
│   └── packages/          # Travel packages
├── templates/             # HTML templates
│   ├── accounts/          # Auth templates
│   ├── core/              # Core templates
│   └── packages/          # Package templates
├── nepal_guide_hub/       # Django settings
├── manage.py
├── requirements.txt
└── pyproject.toml
```

## 🎯 User Flows

### **Tourist Journey**
1. **Mode Selection**: Choose "I'm a Tourist" from landing page
2. **Registration**: Create account with tourist profile
3. **Browse**: Explore packages, guides, and agencies
4. **Book**: Select and book experiences
5. **Review**: Leave ratings and reviews after trips

### **Agency Journey**
1. **Mode Selection**: Choose "I'm an Agency" from landing page
2. **Registration**: Create account with agency details
3. **Verification**: Wait for admin verification
4. **Setup**: Add guides and create packages
5. **Manage**: Handle bookings and customer interactions

### **Navigation Paths**
- **By Packages**: Tourist browses packages → sees agency details and pricing
- **By Guides**: Tourist finds guides → sees ratings, bio, and availability
- **By Agencies**: Tourist explores agencies → sees their guides and packages

## 🎨 Design System

### **Color Palette**
- **Primary Green**: nepal-green-600 (#16a34a)
- **Secondary Green**: nepal-green-500 (#22c55e)
- **Accent Blue**: nepal-blue (#003893)
- **Accent Red**: nepal-red (#DC143C)

### **Components**
- **Cards**: Rounded with hover effects and shadows
- **Buttons**: Gradient backgrounds with smooth transitions
- **Forms**: Clean styling with focus states
- **Navigation**: Sticky header with user-specific menus

## 🛠️ Technology Stack

### **Backend**
- **Django 5.2.6**: Web framework
- **PostgreSQL**: Primary database
- **Python 3.12+**: Programming language

### **Frontend**
- **TailwindCSS**: Utility-first CSS framework
- **Font Awesome**: Icons
- **Vanilla JavaScript**: Interactive elements

### **Key Libraries**
- **django-crispy-forms**: Form styling
- **crispy-tailwind**: TailwindCSS integration
- **python-decouple**: Environment configuration
- **Pillow**: Image handling

## 📱 API Structure

The project uses Django's built-in views and URLs. Key endpoints:

- `/` - Landing page (mode selection)
- `/home/` - Tourist homepage
- `/packages/` - Package listing and details
- `/guides/` - Guide listing and profiles
- `/agencies/` - Agency listing and details
- `/accounts/` - Authentication and profiles
- `/bookings/` - Booking management
- `/admin/` - Django admin panel

## 🔐 Security Features

- **User Authentication**: Django's built-in auth system
- **CSRF Protection**: Enabled across all forms
- **Agency Verification**: Only verified agencies can operate
- **Permission Controls**: User-type specific access controls
- **Input Validation**: Form validation and sanitization

## 🌍 Deployment

### **Production Settings**
- Set `DEBUG=False`
- Configure secure database settings
- Set up static file serving (WhiteNoise or CDN)
- Configure email backend
- Set up SSL/HTTPS
- Use environment variables for secrets

### **Recommended Stack**
- **Server**: DigitalOcean, AWS, or Heroku
- **Database**: PostgreSQL
- **Static Files**: AWS S3 or CDN
- **Email**: SendGrid or AWS SES

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Test specific app
python manage.py test apps.accounts

# Coverage report
coverage run manage.py test
coverage report
```

## 📈 Future Enhancements

### **Immediate (Phase 2)**
- [ ] Payment integration (Stripe/PayPal)
- [ ] Email notifications
- [ ] Advanced search with filters
- [ ] Mobile app (React Native/Flutter)

### **Medium Term (Phase 3)**
- [ ] Multi-language support (Nepali/English)
- [ ] Real-time chat system
- [ ] GPS tracking for guides
- [ ] Social media integration

### **Long Term (Phase 4)**
- [ ] AI-powered recommendations
- [ ] Virtual reality previews
- [ ] Blockchain-based reviews
- [ ] IoT integration for weather/conditions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and Django docs
- **Issues**: Use GitHub Issues for bug reports
- **Contact**: info@nepalguidehub.com

## 🙏 Acknowledgments

- **TailwindCSS** for the amazing utility-first CSS framework
- **Django** community for the robust web framework
- **Font Awesome** for beautiful icons
- **Nepal Tourism Board** for inspiration

---

**Built with ❤️ for Nepal Tourism**

*Discover the majestic beauty of Nepal through verified guides and trusted agencies.*
