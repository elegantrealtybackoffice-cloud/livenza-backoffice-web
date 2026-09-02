import type { Metadata } from 'next'
import styles from '../legal.module.css'

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'Terms governing use of Livenza.life, My Livenza, accommodation discovery and booking, store services and related customer features.',
  alternates: { canonical: 'https://livenza.life/terms' },
  openGraph: { title: 'Terms of Service', description: 'Terms governing use of Livenza.life, My Livenza, accommodation discovery and booking, store services and related customer features.', url: 'https://livenza.life/terms', siteName: 'Livenza.life', type: 'website' },
}

export default function TermsPage() {
  return <main className={styles.page}>
    <section className={styles.hero}>
      <div className={`section-inner ${styles.shell}`}>
        <div className={styles.eyebrow}>LIVENZA.LIFE LEGAL</div>
        <h1>Terms of Service</h1>
        <p className={styles.lead}>These terms govern access to and use of Livenza.life and the digital services made available by Livenza Life LLP.</p>
        <p className={styles.updated}>Last updated: 2 September 2026</p>
      </div>
    </section>

    <div className={`section-inner ${styles.shell} ${styles.content}`}>
      <section className={styles.section}>
        <h2>1. Acceptance</h2>
        <p>By using Livenza.life or creating or using a My Livenza account, you agree to these Terms of Service and any service-specific terms presented to you for a booking, order or other transaction. If you do not agree, do not complete the relevant transaction.</p>
      </section>

      <section className={styles.section}>
        <h2>2. Accounts and authentication</h2>
        <p>You are responsible for providing accurate information and for protecting access to your mobile device and account. Livenza may use mobile OTP authentication, including approved WhatsApp authentication messages. Never share an OTP with another person or with someone claiming to need it on behalf of Livenza.</p>
      </section>

      <section className={styles.section}>
        <h2>3. Accommodation discovery and bookings</h2>
        <p>Property, room, rate, inventory and service information is subject to availability and the terms shown for the selected stay. A booking is not confirmed merely because a page, quote, hold or payment screen was opened. Confirmation depends on the applicable booking flow and authoritative backend status.</p>
        <p>Property-specific booking conditions, rate-plan rules, house rules, cancellation terms, security-deposit terms and signed accommodation agreements, where applicable, form part of the transaction and prevail for that specific booking if they are more specific than these general website terms.</p>
      </section>

      <section className={styles.section}>
        <h2>4. Prices, payments and transaction status</h2>
        <p>Prices and charges shown during a live transaction are subject to the selected service, taxes, add-ons and applicable rate or order terms. Payments may be processed by an external payment provider. A payment or commercial transaction is treated as successful only when the platform records verified backend confirmation, not merely because a browser displays a success state.</p>
      </section>

      <section className={styles.section}>
        <h2>5. Cancellations, refunds and changes</h2>
        <p>Cancellation, refund, credit, relocation and date-change rights depend on the booking, rate plan, property-specific terms, order terms, applicable law and the circumstances of the transaction. Nothing on this general Terms page creates a refund promise that is broader than the specific terms accepted for the booking or order, and nothing here removes a non-waivable consumer right.</p>
      </section>

      <section className={styles.section}>
        <h2>6. Store and merchandise</h2>
        <p>Product availability, variants, stock, delivery options and final order totals are determined by the current store flow. Livenza may refuse or cancel an unfulfilled order where stock is unavailable, payment is not verified, information is materially incorrect or fulfillment would be unlawful, with any resulting refund or reversal handled according to the applicable payment and order status.</p>
      </section>

      <section className={styles.section}>
        <h2>7. Acceptable use</h2>
        <p>You must not misuse the platform, attempt unauthorized access, interfere with security controls, submit another person&apos;s information without authority, use the service for unlawful activity, manipulate bookings or inventory, or attempt to obtain services through fraud or abuse.</p>
      </section>

      <section className={styles.section}>
        <h2>8. Intellectual property</h2>
        <p>Livenza names, logos, interface elements, original content and other brand materials are owned by or licensed to Livenza Life LLP unless stated otherwise. These terms do not transfer ownership rights to users.</p>
      </section>

      <section className={styles.section}>
        <h2>9. Third-party services</h2>
        <p>The platform may depend on payment, messaging, hosting, maps, email, storage or other third-party services. Their availability and separate terms may affect a feature. Livenza is not responsible for a third party&apos;s independent service beyond obligations that cannot lawfully be excluded.</p>
      </section>

      <section className={styles.section}>
        <h2>10. Service availability and liability</h2>
        <p>We work to keep Livenza services accurate and available, but maintenance, connectivity, provider outages, inventory changes or events beyond reasonable control can interrupt a feature. To the maximum extent permitted by law, liability is limited to losses that are legally recoverable and directly connected to Livenza&apos;s obligations. Nothing in these terms excludes liability that cannot lawfully be excluded or limits non-waivable consumer rights.</p>
      </section>

      <section className={styles.section}>
        <h2>11. Governing law</h2>
        <p>These general Terms of Service are governed by the laws of India. Any dispute is subject to applicable consumer-protection rules and mandatory territorial or statutory jurisdiction. Service-specific agreements may contain additional dispute-resolution provisions for the relevant transaction.</p>
      </section>

      <section className={styles.section}>
        <h2>12. Contact</h2>
        <p>Questions about these terms can be sent to <a href="mailto:info@livenzalife.com">info@livenzalife.com</a>.</p>
      </section>
    </div>
  </main>
}
