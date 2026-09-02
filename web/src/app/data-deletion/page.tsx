import type { Metadata } from 'next'
import styles from '../legal.module.css'

export const metadata: Metadata = {
  title: 'Data Deletion',
  description: 'Instructions for requesting deletion of a Livenza account or personal information associated with Livenza.life.',
  alternates: { canonical: 'https://livenza.life/data-deletion' },
  openGraph: { title: 'Data Deletion', description: 'Instructions for requesting deletion of a Livenza account or personal information associated with Livenza.life.', url: 'https://livenza.life/data-deletion', siteName: 'Livenza.life', type: 'website' },
}

export default function DataDeletionPage() {
  return <main className={styles.page}>
    <section className={styles.hero}>
      <div className={`section-inner ${styles.shell}`}>
        <div className={styles.eyebrow}>LIVENZA.LIFE PRIVACY</div>
        <h1>Data Deletion</h1>
        <p className={styles.lead}>You can ask Livenza Life LLP to delete your Livenza account or personal information, subject to records we must or may retain for legitimate legal and operational purposes.</p>
        <p className={styles.updated}>Last updated: 2 September 2026</p>
      </div>
    </section>

    <div className={`section-inner ${styles.shell} ${styles.content}`}>
      <section className={`${styles.section} ${styles.callout}`}>
        <h2>How to submit a request</h2>
        <ol className={styles.list}>
          <li>Email <a href="mailto:info@livenzalife.com?subject=Data%20Deletion%20Request">info@livenzalife.com</a> with the subject <strong>Data Deletion Request</strong>.</li>
          <li>Include the mobile number or email address associated with your Livenza account and your name, only to the extent needed for us to locate the correct account.</li>
          <li>Briefly state whether you want your entire account deleted or are asking about particular information.</li>
          <li>We may ask you to complete a reasonable identity-verification step before acting on a deletion request so that another person cannot delete your account.</li>
        </ol>
      </section>

      <section className={styles.section}>
        <h2>What not to send</h2>
        <p>Never send your password, OTP, card PIN, CVV, banking password or other restricted authentication secret in a deletion request. Livenza does not need those credentials to process a privacy request.</p>
      </section>

      <section className={styles.section}>
        <h2>What happens after a valid request</h2>
        <p>After we identify the relevant account and verify the request where reasonably necessary, we will review the data associated with the request and delete or anonymise information that is no longer required, subject to applicable law and legitimate retention requirements.</p>
      </section>

      <section className={styles.section}>
        <h2>Information that may need to be retained</h2>
        <p>Some booking, payment, invoice, accounting, tax, fraud-prevention, safety, dispute, contractual or legal-compliance records may need to be retained for the applicable period even after account access is closed. Retained records are not kept merely for convenience and remain subject to appropriate access controls.</p>
      </section>

      <section className={styles.section}>
        <h2>Authentication and messaging records</h2>
        <p>Where WhatsApp OTP authentication is used, account deletion does not require you to disclose an OTP to a support representative. Security and delivery records may be retained only where reasonably needed for fraud prevention, security, dispute handling or legal obligations.</p>
      </section>

      <section className={styles.section}>
        <h2>Questions</h2>
        <p>If you are unsure whether deletion is the right request, you may first ask for correction or information about your account by writing to <a href="mailto:info@livenzalife.com">info@livenzalife.com</a>. You can also review our <a href="/privacy">Privacy Policy</a>.</p>
      </section>
    </div>
  </main>
}
