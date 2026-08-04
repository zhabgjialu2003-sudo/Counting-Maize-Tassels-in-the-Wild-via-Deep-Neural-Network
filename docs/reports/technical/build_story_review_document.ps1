param(
    [string]$SourceDocx = (Join-Path $env:USERPROFILE 'Desktop\Preliminary_Technical_Documentation_Extended_User_Stories_Corrected.docx'),
    [string]$DesktopOutput = (Join-Path $env:USERPROFILE 'Desktop\Extension_User_Stories_Review_Copy_English.docx')
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$RepoOutput = Join-Path $RepoRoot 'docs\reports\technical\extension-user-stories-review-copy.docx'
$DataPath = Join-Path $RepoRoot 'docs\requirements\user-story-extension-details.json'
$UmlRoot = Join-Path $RepoRoot 'docs\design\uml\story-extensions'
$UiRoot = Join-Path $RepoRoot 'docs\evidence\user-story-extensions\ui'
$Stories = Get-Content -LiteralPath $DataPath -Raw -Encoding UTF8 | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $SourceDocx)) {
    throw "Source document not found: $SourceDocx"
}

Copy-Item -LiteralPath $SourceDocx -Destination $DesktopOutput -Force

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null

function Find-Start([string]$text) {
    $range = $script:doc.Content.Duplicate
    $find = $range.Find
    $find.ClearFormatting()
    $find.Text = $text
    $find.Forward = $true
    $find.Wrap = 0
    if (-not $find.Execute()) { throw "Could not find: $text" }
    return $range.Start
}

function Delete-BetweenRoleAndStory([string]$roleHeading, [string]$storyHeading) {
    $roleStart = Find-Start $roleHeading
    $storyStart = Find-Start $storyHeading
    $roleParagraph = $script:doc.Range($roleStart, $roleStart).Paragraphs.Item(1).Range
    if ($roleParagraph.End -gt $storyStart) {
        throw "Invalid review range for $roleHeading and $storyHeading"
    }
    $script:doc.Range($roleParagraph.End, $storyStart).Delete() | Out-Null
}

function Replace-ExactText([string]$oldText, [string]$newText) {
    $range = $script:doc.Content.Duplicate
    $find = $range.Find
    $find.ClearFormatting()
    $find.Text = $oldText
    $find.Replacement.ClearFormatting()
    $find.Replacement.Text = $newText
    $find.Forward = $true
    $find.Wrap = 1
    $find.Format = $false
    $find.MatchCase = $true
    $find.Execute($oldText, $false, $false, $false, $false, $false, $true, 1, $false, $newText, 2) | Out-Null
}

function Replace-SequenceImages {
    foreach ($story in $script:Stories) {
        $altText = "$($story.id) Sequence Diagram"
        $target = $null
        foreach ($image in $script:doc.InlineShapes) {
            if ($image.AlternativeText -eq $altText) {
                $target = $image
                break
            }
        }
        if (-not $target) { throw "Sequence image not found: $altText" }

        $slug = $story.id.ToLower().Replace('.', '-')
        $path = Join-Path $script:UmlRoot "$slug\sequence.png"
        if (-not (Test-Path -LiteralPath $path)) { throw "Sequence image missing: $path" }

        $width = $target.Width
        $range = $target.Range.Duplicate
        $target.Delete()
        $replacement = $script:doc.InlineShapes.AddPicture($path, $false, $true, $range)
        $replacement.LockAspectRatio = -1
        $replacement.Width = $width
        $replacement.Title = $altText
        $replacement.AlternativeText = $altText
    }
}

function Replace-UiImages {
    foreach ($story in $script:Stories) {
        $altText = "$($story.id) Current User Interface"
        $target = $null
        foreach ($image in $script:doc.InlineShapes) {
            if ($image.AlternativeText -eq $altText) {
                $target = $image
                break
            }
        }
        if (-not $target) { throw "UI image not found: $altText" }

        $fileStem = $story.id.Replace('.', '_')
        $path = Join-Path $script:UiRoot "$fileStem.png"
        if (-not (Test-Path -LiteralPath $path)) { throw "UI image missing: $path" }

        $width = $target.Width
        $range = $target.Range.Duplicate
        $target.Delete()
        $replacement = $script:doc.InlineShapes.AddPicture($path, $false, $true, $range)
        $replacement.LockAspectRatio = -1
        $replacement.Width = $width
        $replacement.Title = $altText
        $replacement.AlternativeText = $altText
    }
}

try {
    $doc = $word.Documents.Open($DesktopOutput, $false, $false)
    $script:doc = $doc
    $script:Stories = $Stories
    $script:UmlRoot = $UmlRoot
    $script:UiRoot = $UiRoot

    $locks = @{}
    foreach ($control in $doc.ContentControls) {
        $key = "$($control.ID)"
        $locks[$key] = @($control.LockContents, $control.LockContentControl)
        $control.LockContents = $false
        $control.LockContentControl = $false
    }

    $activityStart = Find-Start 'Activity diagram'
    $doc.Range($activityStart, $doc.Content.End - 1).Delete() | Out-Null

    Delete-BetweenRoleAndStory 'E. System (8 User Stories)' 'E.6  Validate and Isolate Every Upload'
    Delete-BetweenRoleAndStory 'D. Admin (9 User Stories)' 'D.7  Assign Agronomists to Fields'
    Delete-BetweenRoleAndStory 'C. Agronomist (8 User Stories)' 'C.6  Review Assigned Field Evidence'
    Delete-BetweenRoleAndStory 'B. Researcher (9 User Stories)' 'B.7  Review Uncertainty and Provenance'
    Delete-BetweenRoleAndStory 'A. Farmer (11 User Stories)' 'A.9  Bilingual Leaf Screening'

    $farmerStart = Find-Start 'A. Farmer (11 User Stories)'
    $doc.Range(0, $farmerStart).Delete() | Out-Null

    Replace-ExactText 'A. Farmer (11 User Stories)' 'A. Farmer (3 Extension User Stories)'
    Replace-ExactText 'B. Researcher (9 User Stories)' 'B. Researcher (3 Extension User Stories)'
    Replace-ExactText 'C. Agronomist (8 User Stories)' 'C. Agronomist (3 Extension User Stories)'
    Replace-ExactText 'D. Admin (9 User Stories)' 'D. Admin (3 Extension User Stories)'
    Replace-ExactText 'E. System (8 User Stories)' 'E. System (3 Extension User Stories)'

    Replace-SequenceImages
    Replace-UiImages

    $intro = $doc.Range(0, 0)
    $intro.Text = "Extension User Stories - Review Copy`rNewly added stories only: A.9-A.11, B.7-B.9, C.6-C.8, D.7-D.9 and E.6-E.8.`r`r"
    $title = $doc.Paragraphs.Item(1).Range
    $title.Font.Name = 'Calibri'
    $title.Font.Size = 18
    $title.Font.Bold = 1
    $title.Font.Color = 12611584
    $title.ParagraphFormat.SpaceAfter = 6
    $subtitle = $doc.Paragraphs.Item(2).Range
    $subtitle.Font.Name = 'Cambria'
    $subtitle.Font.Size = 11
    $subtitle.Font.Color = 6908265
    $subtitle.ParagraphFormat.SpaceAfter = 12

    foreach ($control in $doc.ContentControls) {
        $key = "$($control.ID)"
        if ($locks.ContainsKey($key)) {
            $control.LockContents = [bool]$locks[$key][0]
            $control.LockContentControl = [bool]$locks[$key][1]
        }
    }

    $doc.Fields.Update() | Out-Null
    $doc.RemoveDocumentInformation(4)
    $doc.Save()
    $pages = $doc.ComputeStatistics(2)
    $doc.Close($false)
    $doc = $null
    Copy-Item -LiteralPath $DesktopOutput -Destination $RepoOutput -Force
    Write-Output "Completed: $DesktopOutput"
    Write-Output "Repository copy: $RepoOutput"
    Write-Output "Pages: $pages"
}
finally {
    if ($doc) { $doc.Close($false) }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
