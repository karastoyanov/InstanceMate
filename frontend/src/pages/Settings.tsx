import LlmSettingsSection from '../components/LlmSettingsSection'
import ServiceNowSettingsSection from '../components/ServiceNowSettingsSection'

function Settings() {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <h1 className="text-2xl font-semibold text-foreground">Settings</h1>
      <ServiceNowSettingsSection />
      <LlmSettingsSection />
    </div>
  )
}

export default Settings
