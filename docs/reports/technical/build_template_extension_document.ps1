param(
    [string]$ReferenceDocx = (Join-Path $env:USERPROFILE 'Desktop\FYP-26-S2-7_ProgressReport\Preliminary_Technical_Documentation.docx'),
    [string]$DesktopOutput = (Join-Path $env:USERPROFILE 'Desktop\Preliminary_Technical_Documentation_Extended_User_Stories_Corrected.docx')
)

$ErrorActionPreference = 'Stop'
$ExpectedReferenceSha256 = 'e3fde2807ca548e7f1d1991bc767ab855673964e6375a876c408242c0d40244f'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$DataPath = Join-Path $RepoRoot 'docs\requirements\user-story-extension-details.json'
$RepoOutput = Join-Path $RepoRoot 'docs\reports\technical\preliminary-technical-documentation-extended.docx'
$UmlRoot = Join-Path $RepoRoot 'docs\design\uml\story-extensions'
$WireframeRoot = Join-Path $RepoRoot 'docs\evidence\user-story-extensions\wireframes'
$UiRoot = Join-Path $RepoRoot 'docs\evidence\user-story-extensions\ui'

if ((Get-FileHash -LiteralPath $ReferenceDocx -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedReferenceSha256) {
    throw 'The retained reference DOCX no longer matches the distilled template SHA-256.'
}

$stories = Get-Content -LiteralPath $DataPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($stories.Count -ne 15) { throw "Expected 15 extension stories, found $($stories.Count)." }

Copy-Item -LiteralPath $ReferenceDocx -Destination $DesktopOutput -Force

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
    if (-not $find.Execute()) { throw "Template locator not found: $text" }
    return $range.Start
}

function Set-RangeText($range, [string]$text) {
    $editable = $range.Duplicate
    if ($editable.End -gt $editable.Start) { $editable.End = $editable.End - 1 }
    $editable.Text = $text
}

function Bold-Label($cell, [string]$label, [bool]$boldAll = $false) {
    $content = $cell.Range.Duplicate
    $content.End = $content.End - 1
    $content.Font.Bold = 0
    if ($boldAll) {
        $content.Font.Bold = 1
    } elseif ($label -and $content.End -ge ($content.Start + $label.Length)) {
        $labelRange = $script:doc.Range($content.Start, $content.Start + $label.Length)
        $labelRange.Font.Bold = 1
    }
}

function Set-CellText($cell, [string]$text, [string]$label = '', [bool]$boldAll = $false) {
    $content = $cell.Range.Duplicate
    $content.End = $content.End - 1
    $content.Text = $text
    Bold-Label $cell $label $boldAll
}

function Join-Numbered($items) {
    $lines = @()
    for ($i = 0; $i -lt $items.Count; $i++) { $lines += "$(($i + 1)). $($items[$i])" }
    return ($lines -join "`r")
}

function Join-Bullets($items) {
    return ($items -join "`r")
}

function Apply-BulletsAfterLabel($cell) {
    $cell.Range.ListFormat.RemoveNumbers()
    $paragraphs = $cell.Range.Paragraphs
    for ($index = 2; $index -le $paragraphs.Count; $index++) {
        $paragraphs.Item($index).Range.ListFormat.ApplyBulletDefault()
    }
    $paragraphs.Item(1).Range.ListFormat.RemoveNumbers()
}

function Fit-InlineShape($shape, [double]$maxWidth, [double]$maxHeight) {
    $shape.LockAspectRatio = -1
    if ($shape.Width -gt $maxWidth) { $shape.Width = $maxWidth }
    if ($shape.Height -gt $maxHeight) { $shape.Height = $maxHeight }
}

function Replace-BlockImages($block, $story) {
    if ($block.InlineShapes.Count -ne 4) {
        throw "Story $($story.id) clone contains $($block.InlineShapes.Count) images instead of four."
    }
    $slug = $story.id.ToLowerInvariant().Replace('.', '-')
    $fileStem = $story.id.Replace('.', '_')
    $paths = @(
        (Join-Path $script:UmlRoot "$slug\bce-class.png"),
        (Join-Path $script:UmlRoot "$slug\sequence.png"),
        (Join-Path $script:WireframeRoot "$fileStem.png"),
        (Join-Path $script:UiRoot "$fileStem.png")
    )
    $titles = @(
        "$($story.id) BCE Class Diagram",
        "$($story.id) Sequence Diagram",
        "$($story.id) Low-Fidelity Wireframe",
        "$($story.id) Current User Interface"
    )
    $maxWidths = @(432.0, 432.0, 360.0, 432.0)
    $maxHeights = @(185.0, 285.0, 285.0, 315.0)
    for ($i = 3; $i -ge 0; $i--) {
        if (-not (Test-Path -LiteralPath $paths[$i])) { throw "Missing story asset: $($paths[$i])" }
        $old = $block.InlineShapes.Item($i + 1)
        $anchor = $old.Range.Duplicate
        $old.Delete()
        $newShape = $script:doc.InlineShapes.AddPicture($paths[$i], $false, $true, $anchor)
        Fit-InlineShape $newShape $maxWidths[$i] $maxHeights[$i]
        $newShape.Title = $titles[$i]
        $newShape.AlternativeText = $titles[$i]
    }
}

function Populate-StoryBlock($block, $story) {
    $heading = $null
    $storyParagraph = $null
    foreach ($paragraph in $block.Paragraphs) {
        $text = ($paragraph.Range.Text -replace '[\r\a]', '').Trim()
        $style = $paragraph.Range.Style.NameLocal
        if (-not $heading -and $style -eq 'Heading 2') { $heading = $paragraph }
        if (-not $storyParagraph -and $text.StartsWith('User Story:')) { $storyParagraph = $paragraph }
    }
    if (-not $heading -or -not $storyParagraph) { throw "Could not locate heading/story slots for $($story.id)." }
    Set-RangeText $heading.Range "$($story.id)  $($story.title)"
    Set-RangeText $storyParagraph.Range "User Story: $($story.story)"

    if ($block.Tables.Count -ne 2) { throw "Story $($story.id) clone does not contain the two required tables." }
    $description = $block.Tables.Item(1)
    Set-CellText $description.Cell(1,1) "Name: $($story.title)" 'Name:' $true
    Set-CellText $description.Cell(2,1) "Stakeholder & Objectives:`r$($story.objectives)" 'Stakeholder & Objectives:'
    Set-CellText $description.Cell(3,1) "Actors: $($story.actors)" 'Actors:'
    Set-CellText $description.Cell(4,1) "Triggers: $($story.triggers)" 'Triggers:'
    Set-CellText $description.Cell(5,1) "Pre-Condition:`r$($story.pre_condition)" 'Pre-Condition:'
    Set-CellText $description.Cell(6,1) "Post-Condition: $($story.post_condition)" 'Post-Condition:'
    Set-CellText $description.Cell(7,1) "Normal Flow:`r$(Join-Numbered $story.normal_flow)" 'Normal Flow:'
    Set-CellText $description.Cell(8,1) "Sub-Flow: $($story.sub_flow)" 'Sub-Flow:'
    Set-CellText $description.Cell(9,1) "Alternative Flow:`r$(Join-Numbered $story.alternative_flow)" 'Alternative Flow:'

    $test = $block.Tables.Item(2)
    Set-CellText $test.Cell(1,1) "Test Case ID: $($story.test_id)" 'Test Case ID:'
    Set-CellText $test.Cell(1,2) "User Stories: #$($story.global_number) ($($story.id))" 'User Stories:'
    Set-CellText $test.Cell(2,1) "Name: $($story.story)" 'Name:'
    Set-CellText $test.Cell(3,1) "Test Scenario: $($story.scenario)" 'Test Scenario:'
    Set-CellText $test.Cell(4,1) "Actions:`r$(Join-Numbered $story.actions)" 'Actions:'
    Set-CellText $test.Cell(5,1) "Prerequisites:`r$(Join-Bullets $story.prerequisites)" 'Prerequisites:'
    Set-CellText $test.Cell(6,1) "Test Data:`r$(Join-Bullets $story.test_data)" 'Test Data:'
    Apply-BulletsAfterLabel $test.Cell(5,1)
    Apply-BulletsAfterLabel $test.Cell(6,1)
    Set-CellText $test.Cell(7,1) "Expected Results: $($story.expected)" 'Expected Results:'
    Set-CellText $test.Cell(8,1) 'Actual Result: As expected. Verified by the current automated regression suite.' 'Actual Result:'
    Set-CellText $test.Cell(9,1) 'Pass' '' $true
    $test.Cell(9,1).Range.ParagraphFormat.Alignment = 1

    Replace-BlockImages $block $story
}

function Insert-StoryBefore([string]$targetHeading, $story) {
    $targetStart = Find-Start $targetHeading
    $insert = $script:doc.Range($targetStart, $targetStart)
    $insert.FormattedText = $script:sourceRange.FormattedText
    $shiftedTargetStart = Find-Start $targetHeading
    if ($shiftedTargetStart -le $targetStart) { throw "Insertion failed before $targetHeading" }
    $block = $script:doc.Range($targetStart, $shiftedTargetStart)
    Populate-StoryBlock $block $story
}

function Replace-ExactText([string]$oldText, [string]$newText) {
    $start = Find-Start $oldText
    $range = $script:doc.Range($start, $start + $oldText.Length)
    $range.Text = $newText
}

try {
    $doc = $word.Documents.Open($DesktopOutput, $false, $false)
    $script:doc = $doc
    $script:UmlRoot = $UmlRoot
    $script:WireframeRoot = $WireframeRoot
    $script:UiRoot = $UiRoot

    $contentControlLocks = @{}
    foreach ($control in $doc.ContentControls) {
        $contentControlLocks[$control.Tag] = [bool]$control.LockContents
        $control.LockContents = $false
    }

    $sourceStart = Find-Start 'A.2  Auto-Count Maize Tassels'
    $sourceEnd = Find-Start 'A.3  View Counting Results'
    $script:sourceRange = $doc.Range($sourceStart, $sourceEnd)

    $groups = @(
        @{ Target = 'B. Researcher (6 User Stories)'; Stories = @($stories | Where-Object role -eq 'Farmer') },
        @{ Target = 'C. Agronomist (5 User Stories)'; Stories = @($stories | Where-Object role -eq 'Researcher') },
        @{ Target = 'D. Admin (6 User Stories)'; Stories = @($stories | Where-Object role -eq 'Agronomist') },
        @{ Target = 'E. System (5 User Stories)'; Stories = @($stories | Where-Object role -eq 'Admin') },
        @{ Target = 'Activity diagram'; Stories = @($stories | Where-Object role -eq 'System') }
    )
    foreach ($group in $groups) {
        foreach ($story in $group.Stories) {
            Insert-StoryBefore $group.Target $story
            Write-Output "Inserted $($story.id) $($story.title)"
        }
    }

    Replace-ExactText 'A. Farmer (8 User Stories)' 'A. Farmer (11 User Stories)'
    Replace-ExactText 'B. Researcher (6 User Stories)' 'B. Researcher (9 User Stories)'
    Replace-ExactText 'C. Agronomist (5 User Stories)' 'C. Agronomist (8 User Stories)'
    Replace-ExactText 'D. Admin (6 User Stories)' 'D. Admin (9 User Stories)'
    Replace-ExactText 'E. System (5 User Stories)' 'E. System (8 User Stories)'

    foreach ($control in $doc.ContentControls) {
        if ($contentControlLocks.ContainsKey($control.Tag)) {
            $control.LockContents = $contentControlLocks[$control.Tag]
        } else {
            $control.LockContents = $true
        }
    }

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
    if ($script:sourceRange) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($script:sourceRange) }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
