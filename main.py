Esta es la Especificación Maestra de Prompt (Master Prompt Specification).
Este prompt está diseñado para que no se pierda ni un solo detalle de la lógica, el diseño, la paleta de colores y el flujo de negocio que tiene tu aplicación actual en React. Al pasárselo a una IA (como GPT-4o, Claude 3.5 Sonnet o Gemini 1.5 Pro), debería ser capaz de replicar la app (ya sea en Streamlit, o en otro framework) con una fidelidad del 99%.
Copia y pega el siguiente bloque en inglés (para máxima precisión técnica) en el chat de la IA:
🚀 MASTER PROMPT: "JM Alquiler Premium - Triple Frontera VIP"
Role: You are a Senior Full-Stack Engineer and UI/UX Designer specializing in building luxury web applications.
Objective: Recreate a high-end Car Rental Management System called "JM Alquiler". The app must exude luxury, reliability, and technical sophistication.
Tech Stack: [Insert Target Framework here, e.g., Python Streamlit / React / Next.js]
Language: The UI text must be in Spanish.
1. Visual Identity & Design System (CRITICAL)
You must strictly adhere to this design system to match the brand identity.
Theme: "Executive Luxury", "Triple Frontera VIP", "Glassmorphism".
Color Palette:
Primary (Bordo): #600010 (Deep Wine/Burgundy)
Accent (Gold): #D4AF37 (Metallic Gold)
Background: #FDFCFB (Ivory/Cream/Off-white)
Text: Inter font (Body), Playfair Display (Headings/Titles).
Styling Rules:
All cards and containers must have heavy rounding: border-radius: 2rem or 3rem.
Use Glassmorphism for headers (Blur effects).
Buttons must be uppercase, tracking-wide (letter-spacing: 0.2em), and bold.
Animations: Elements must fade-in. Car images should have a slight "float" animation.
2. Core Data & Initialization
Persistence: Use local state/session storage to save Reservations and Expenses.
Currency Logic:
Base currency is BRL (Reais).
Fetch live exchange rates (BRL -> PYG / USD) using open.er-api.com.
Fallback rate: 1 BRL = 1450 PYG.
Display prices in both BRL and PYG (Guaraníes) throughout the app.
Initial Fleet Data:
Initialize the database with these exact vehicles:
Hyundai Tucson 2012 (Price: 260 BRL, Diesel, Auto, Plate: AAVI502, Img: "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png")
Toyota Vitz 2012 (Price: 195 BRL, Gas, Auto, Plate: AAVP719, Img: "https://i.ibb.co/Y7ZHY8kX/pngegg.png")
Toyota Vitz RS 2012 (Price: 210 BRL, Gas, Sequential, Plate: AAOR725, Img: "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png")
Toyota Voxy 2011 (Price: 240 BRL, Gas, 7-seater, Plate: AAUG465, Img: "https://i.ibb.co/VpSpSJ9Q/voxy.png")
3. Application Modules (Functionality)
A. Tab 1: "Unidades" (Client Facing)
Hero Section:
Large banner with specific text: "Domina el Camino." and "Calidad Certificada MERCOSUR".
Background pattern (leather texture) + Gold blur accents.
Vehicle Catalog (Grid):
Display the fleet in cards.
Card Features:
Show Status Pill (Available = Green/Pulse, Maintenance = Red).
Flip/Expand functionality: Clicking "Info" toggles detailed specs (Motor, Safety, Trunk size).
Availability Calendar: Inside the card, show a mini-calendar highlighting reserved dates in Red.
Action: "Gestionar Reserva" button (Disabled if in Maintenance). Opens the Booking Wizard.
B. The Booking Wizard (Complex Logic)
A modal/overlay with 3 distinct steps:
Step 1: Cronograma (Schedule):
Inputs: Start Date/Time, End Date/Time.
Validations:
Cannot select past dates.
Office Hours: Mon-Fri (08:00-17:00), Sat-Sun (08:00-12:00). Warn user if outside these hours.
Conflict Check: Prevent booking if dates overlap with an existing reservation for that car.
Show financial summary: Total Days, Total Cost (BRL), and Reservation Fee (1 Day cost).
Step 2: Portal de Pagos (Payments):
User inputs: Name, ID (CI/RG), Payment Method.
Methods:
QR Bancard / PIX: Generate a dynamic QR code image using api.qrserver.com.
Credit Card: Show a cosmetic credit card input form.
Transfer: Show bank details (Ueno Bank / Santander).
Proof: Allow user to upload an image (Proof of payment).
Step 3: Contrato (Contract):
Display a generated legal contract text summarizing the deal.
Signature Pad: Allow the user to draw their signature.
"Accept Terms" checkbox.
Final Action:
Save reservation.
Redirect to WhatsApp (https://wa.me/595991681191) with a pre-formatted message containing all booking details.
C. Tab 2: "Sede Central" (Location)
Visual display of contact info, Google Maps link, and address in "Ciudad del Este".
Design must look like a premium contact card.
D. Tab 3: "Admin Dashboard" (Protected)
Authentication: Simple password gate (Key: "8899").
KPI Cards: Total Revenue (BRL/PYG), Total Expenses, Net Profit.
Charts:
Area Chart: Income over time.
Pie Chart: Revenue share per vehicle.
AI Business Analyst (Gemini Integration):
Button: "Generar Reporte de Estrategia".
Action: Send fleet status + revenue/expense data to google-generativeai (Model: gemini-2.5-flash).
Prompt: Ask for 3 actionable business tips based on the data.
Expense Manager:
Form to add expenses.
Toggle to input amount in PYG (convert to BRL automatically) or BRL.
Table listing expenses with delete option.
Manual Reservation / Calendar Block:
A form to manually add bookings (e.g., "Old Contracts" or walk-in clients) to block dates in the system.
4. Technical Nuances
Error Handling: If the app crashes, show a custom "JM System Alert" screen (Red background) with a "Reset System" button.
Responsiveness: The layout must be fully responsive (Mobile/Desktop).
Icons: Use lucide-react (or equivalent library) for icons like Car, Shield, MapPin, BrainCircuit (AI).
5. Deliverable
Generate the complete code structure required to run this application. Focus heavily on replicating the CSS/Styling described in Section 1 to ensure the "Luxury" feel is preserved.