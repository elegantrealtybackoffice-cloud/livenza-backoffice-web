import type { Metadata } from 'next'
import styles from '../legal.module.css'

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'How Livenza Life LLP handles personal information across Livenza.life, My Livenza, stays, orders, support and account authentication.',
  alternates: { canonical: 'https://livenza.life/privacy' },
  openGraph: { title: 'Privacy Policy', description: 'How Livenza Life LLP handles personal information across Livenza.life, My Livenza, stays, orders, support and account authentication.', url: 'https://livenza.life/privacy', siteName: 'Livenza.life', type: 'website' },
}

export default function PrivacyPage() {
  return <main className={styles.page}>
    <section className={styles.hero}>
      <div className={`section-inner ${styles.shell}`}>
        <div className={styles.eyebrow}>LIVENZA.LIFE LEGAL</div>
        <h1>Privacy Policy</h1>
        <p className={styles.lead}>This policy explains how Livenza Life LLP processes personal information when you use Livenza.life, My Livenza, accommodation, store, support and related digital services.</p>
        <p className={styles.updated}>Last updated: 2 September 2026</p>
      </div>
    </section>

    <div className={`section-inner ${styles.shell} ${styles.content}`}>
      <section className={styles.section}>
        <h2>1. Who we are</h2>
        <p>Livenza Life LLP operates the Livenza.life lifestyle platform and related Livenza services. Questions about this policy or your personal information can be sent to <a href="mailto:info@livenzalife.com">info@livenzalife.com</a>.</p>
      </section>

      <section className={styles.section}>
        <h2>2. Information we may collect</h2>
        <p>We collect or receive information that is reasonably needed to provide the service you choose. Depending on your relationship with Livenza, this may include:</p>
        <ul className={styles.list}>
          <li>name, mobile number, email address and basic profile information;</li>
          <li>account and authentication records, including mobile-number verification and OTP request or verification events;</li>
          <li>stay and booking information such as property, room or room category, dates, guest or resident details and service selections;</li>
          <li>guardian, college, employer, address or KYC information where it is required for a particular stay or service;</li>
          <li>store order, delivery address, product, size or variant information;</li>
          <li>payment references, payment status and transaction records received from payment providers;</li>
          <li>support requests, service complaints and communications with Livenza;</li>
          <li>technical, security and usage information generated when you use the website, to the extent collected by our hosting, security or analytics systems.</li>
        </ul>
      </section>

      <section className={styles.section}>
        <h2>3. How we use information</h2>
        <p>We process information to operate and secure the platform, authenticate users, manage bookings and orders, provide accommodation and customer support, process payments through configured providers, send service communications, prevent misuse or fraud, maintain records and comply with applicable legal obligations.</p>
        <p>Where My Livenza uses WhatsApp authentication, your mobile number and the one-time verification code are used to deliver the authentication message through the configured WhatsApp service. OTPs are security credentials and should never be shared with another person.</p>
      </section>

      <section className={styles.section}>
        <h2>4. Service providers and sharing</h2>
        <p>We may use service providers for hosting, database or object storage, payment processing, messaging, email, analytics, security and customer-support operations. They receive information only as needed for the relevant service and are subject to their own legal and contractual responsibilities.</p>
        <p>We may also disclose information where required by law, a lawful authority, a court or regulatory process, or where reasonably necessary to protect customers, staff, property, the platform or legal rights.</p>
      </section>

      <section className={styles.section}>
        <h2>5. Payments</h2>
        <p>Payment transactions may be handled by third-party payment providers. Livenza records the transaction information needed to reconcile and support a booking or order, such as payment references and status. Do not send card PINs, CVVs, banking passwords or other restricted authentication secrets to Livenza support.</p>
      </section>

      <section className={styles.section}>
        <h2>6. Cookies, sessions and analytics</h2>
        <p>The site may use cookies, browser storage or similar technologies that are necessary for login, security, session continuity and user preferences. Analytics may be used where configured to understand service performance and customer journeys. We do not describe optional tracking as mandatory when it is not required for the service.</p>
      </section>

      <section className={styles.section}>
        <h2>7. Retention</h2>
        <p>We keep personal information only for as long as reasonably needed for the purpose for which it was collected and for operational, contractual, accounting, tax, fraud-prevention, dispute-resolution, safety and legal-compliance requirements. Records that are no longer required may be deleted or anonymised where appropriate.</p>
      </section>

      <section className={styles.section}>
        <h2>8. Security</h2>
        <p>We use reasonable administrative and technical safeguards appropriate to the information and service, including access controls and protected server-side credentials. No internet service can guarantee absolute security, so customers should also protect their devices, sessions and OTPs.</p>
      </section>

      <section className={styles.section}>
        <h2>9. Your choices and requests</h2>
        <p>You may contact us to request access, correction or deletion of personal information, subject to applicable law and records we are required or permitted to retain. For deletion instructions, see <a href="/data-deletion">Data Deletion</a>.</p>
      </section>

      <section className={styles.section}>
        <h2>10. Changes to this policy</h2>
        <p>We may update this policy as Livenza services, legal requirements or processing practices change. The current version will be published on this page with its updated date.</p>
      </section>
    </div>
  </main>
}
