function normalizeActionTitle(typeName: string, props: Record<string, unknown>): string {
  if (typeof props.title === 'string' && props.title.trim().length > 0) {
    return props.title.trim()
  }

  switch (typeName) {
    case 'Action.CopyToClipboard':
      return 'Copy to Clipboard'
    case 'Action.Paste':
      return 'Paste'
    case 'Action.OpenInBrowser':
      return 'Open in Browser'
    case 'Action.Push':
      return 'Open'
    case 'Action.Pop':
      return 'Back'
    case 'Action.ShowInFinder':
      return 'Show in Finder'
    case 'Action.SubmitForm':
      return 'Submit'
    default:
      return 'Action'
  }
}
