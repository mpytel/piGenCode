# piSplitJoin functions - synced from existing code
import re


def piSplitStr(text: str) -> list[str]:
    """
    Splits a string into tokens based on specified rules, handling encoding,
    whitespace, punctuation, paths, various casing conventions, list indicators,
    and interpreted escape characters.

    Args:
        text (str): The input string to be tokenized.

    Returns:
        list: A list of tokens.
    """
    # Step 1: Decode the text using unicode_escape if it contains potential escape sequences.
    # This interprets sequences like '\n' as actual newlines and '\033[31m' as ANSI escape chars.
    # The user's prompt implies that these should be interpreted before tokenization.

    processed_text = _decode_text_if_needed(text)

    # Define the regex pattern for tokenization. Order matters: longer, more specific
    # patterns should appear earlier to ensure they are matched preferentially.
    token_pattern = re.compile(r"""
        # 1. Full and relative file paths (e.g., /Users/primwind/proj/dev/pi/tcron.sh, piSeed002.pi)
        # This covers paths starting with drive letters, '/', './', '../', and includes filenames.
        (?:
            # Path start: drive letter + separator, or /, ~/, ./, ../
            (?:[a-zA-Z]:[\\/]|[/~.]|[.]{1,2}[/])
            # Path segments (allowing alphanumeric, underscores, hyphens, dots, spaces, followed by separator)
            (?:[a-zA-Z0-9_\-. ]+[\\/])*
            # Filename (allowing alphanumeric, underscores, hyphens, dots, spaces, followed by common extensions)
            [a-zA-Z0-9_\-. ]+\.(?:pi|txt|json|sh|png)
        )
        |
        # Filenames that are not necessarily part of a longer path but have extensions (e.g., piSeed002.pi)
        ([a-zA-Z0-9_\-]+\.(?:pi|txt|json|sh|png))
        |
        # Directory paths that don't end in a specific file extension
        (?:
            (?:[a-zA-Z]:[\\/]|[/~.]|[.]{1,2}[/]) # Starts with drive letter, /, ~/, ./, ../
            (?:[a-zA-Z0-9_\-. ]+[\\/])          # Directory segments
            [a-zA-Z0-9_\- ]+                    # Last segment (directory name)
        )
        # 2. Markdown elements (ordered by specificity/length)
        | (!\[.*?\]\(.*?\))           # ![alt text](url) - image links
        | (\[.*?\]\(.*?\))            # [link text](url) - standard links
        | (\*\*.*?\*\*)               # **bold text**
        | (~~.*?~~)                   # ~~strikethrough~~
        | (`[^`\n]*?`)                # `inline code` (non-greedy, stops at newline/backtick)
        | (\*[^*]+\*|\_[^_]+\_)       # *italic* or _italic_ (non-greedy, ensures not bold/strong)
        | ([a-zA-Z0-9_]+\^.+?\^)      # X^2^ (word/number followed by ^...^)
        | (^-{3,}$|^\*{3,}$|^_{3,}$$) # Horizontal Rules (matches whole line: ---, ***, ___)
        | (^\s*\#{1,6}\s*)             # # Heading (matches # and space at line start, up to 6 hashes)
        | (^\s*>\s*)                  # > Blockquote (matches > and space at line start)

        # 3. Custom identifiers like 'pi<typeName>Body'
        | ([a-zA-Z0-9_]+<[a-zA-Z0-9_]+>[a-zA-Z0-9_]+)

        # 4. ANSI escape codes (e.g., \x1b[31m, after unicode_escape these are actual control characters)
        | (\x1b\[[0-9;]*m)

        # 5. Zero-padded words (e.g., test0023, ZeroPaddedWord00)
        # Matches words containing letters, optionally numbers, then zero-padded digits, then optionally more chars.
        | ([a-zA-Z]+[0-9]*0+\d+[a-zA-Z0-9]*)

        # 6. List indicators (e.g., 1., b., 1), 3}, J])
        # Covers digit. , word. , (digit or word)) , (digit or word)} , (word)]
        | (\d+\.|\w\.|(\d+|\w)[\)\]\}])

        # 7. Case convention words (camelCase, PascalCase, snake_case, Kebab-case)
        # Order matters: longest match first.
        | ([a-z]+(?:[A-Z][a-z0-9]*)*)                  # camelCase (e.g., myVariable)
        | ([A-Z][a-z0-9]*(?:[A-Z][a-z0-9]*)*)           # PascalCase (e.g., MyClass)
        | ([a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*)              # snake_case (e.g., my_variable)
        | ([a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*)              # Kebab-case (e.g., my-variable)

        # 8. Individual punctuation and bracketing characters
        # Includes standard and 'smart' quotes, and the asterisk '*'.
        | ([.,!?;:(){}\[\]<>"'`‘“'”*])

        # 9. Specific whitespace characters (newline, carriage return, tab, form feed) as tokens
        # These are now actual characters after unicode_escape.
        | ([\n\r\t\f])

        # 10. General whitespace (spaces)
        | (\s+) # Capture sequences of one or more spaces

        # 11. Any remaining sequence of non-whitespace characters (catch-all for symbols or other words)
        | ([^\s]+)

        """, re.VERBOSE)

    tokens = []
    last_end = 0

    # Iterate through all non-overlapping matches found by the pattern
    for match in token_pattern.finditer(processed_text):
        start, end = match.span()

        # Check for any text between the last match and the current one.
        # This acts as a safeguard; ideally, a comprehensive regex should leave no gaps.
        if start > last_end:
            unmatched_segment = processed_text[last_end:start]
            if unmatched_segment: # Add if there was any unmatched text
                tokens.append(unmatched_segment)

        # Add the entire matched substring as a token
        tokens.append(match.group(0))
        last_end = end

    # After the loop, add any trailing text that was not matched
    if last_end < len(processed_text):
        trailing_text = processed_text[last_end:]
        if trailing_text:
            tokens.append(trailing_text)

    return tokens

def piJoinList(tokens: list[str]) -> str:
    """
    Recombines a list of tokens into a single string.
    Since piSplitStr is designed to extract *all* elements including
    whitespace and punctuation as distinct tokens, the join operation is a simple
    concatenation. This ensures perfect reconstruction given a correctly
    tokenized list.

    Args:
        tokens (list): A list of tokens.

    Returns:
        str: The recombined string.
    """
    return "".join(tokens)


def piSkipToken(aToken) -> bool:
    token_pattern = re.compile(r"""
        # 1. Full and relative file paths (e.g., /Users/primwind/proj/dev/pi/tcron.sh, piSeed002.pi)
        # This covers paths starting with drive letters, '/', './', '../', and includes filenames.
        (?:
            # Path start: drive letter + separator, or /, ~/, ./, ../
            (?:[a-zA-Z]:[\\/]|[/~.]|[.]{1,2}[/])
            # Path segments (allowing alphanumeric, underscores, hyphens, dots, spaces, followed by separator)
            (?:[a-zA-Z0-9_\-. ]+[\\/])*
            # Filename (allowing alphanumeric, underscores, hyphens, dots, spaces, followed by common extensions)
            [a-zA-Z0-9_\-. ]+\.(?:pi|txt|json|sh|png)
        )
        |
        # Filenames that are not necessarily part of a longer path but have extensions (e.g., piSeed002.pi)
        ([a-zA-Z0-9_\-]+\.(?:pi|txt|json|sh|png))
        |
        # Directory paths that don't end in a specific file extension
        (?:
            (?:[a-zA-Z]:[\\/]|[/~.]|[.]{1,2}[/]) # Starts with drive letter, /, ~/, ./, ../
            (?:[a-zA-Z0-9_\-. ]+[\\/])          # Directory segments
            [a-zA-Z0-9_\- ]+                    # Last segment (directory name)
        )

        # 2. Markdown elements (ordered by specificity/length)
        # | (!\[.*?\]\(.*?\))           # ![alt text](url) - image links
        # | (\[.*?\]\(.*?\))            # [link text](url) - standard links
        # | (\*\*.*?\*\*)               # **bold text**
        # | (~~.*?~~)                   # ~~strikethrough~~
        # | (`[^`\n]*?`)                # `inline code` (non-greedy, stops at newline/backtick)
        # | (\*[^*]+\*|\_[^_]+\_)       # *italic* or _italic_ (non-greedy, ensures not bold/strong)
        # | ([a-zA-Z0-9_]+\^.+?\^)      # X^2^ (word/number followed by ^...^)
        # | (^-{3,}$|^\*{3,}$|^_{3,}$$) # Horizontal Rules (matches whole line: ---, ***, ___)
        # | (^\s*#{1,6}\s*)             # # Heading (matches # and space at line start, up to 6 hashes)
        # | (^\s*>\s*)                  # > Blockquote (matches > and space at line start)

        # 3. Custom identifiers like 'pi<typeName>Body'
        | ([a-zA-Z0-9_]+<[a-zA-Z0-9_]+>[a-zA-Z0-9_]+)

        # 4. ANSI escape codes (e.g., \x1b[31m, after unicode_escape these are actual control characters)
        | (\x1b\[[0-9;]*m)

        # 5. Zero-padded words (e.g., test0023, ZeroPaddedWord00)
        # Matches words containing letters, optionally numbers, then zero-padded digits, then optionally more chars.
        | ([a-zA-Z]+[0-9]*0+\d+[a-zA-Z0-9]*)

        # 6. List indicators (e.g., 1., b., 1), 3}, J])
        # Covers digit. , word. , (digit or word)) , (digit or word)} , (word)]
        | (\d+\.|\w\.|(\d+|\w)[\)\]\}])

        # 7. Case convention words (camelCase, PascalCase, snake_case, Kebab-case)
        # Order matters: longest match first.
        # | ([a-z]+(?:[A-Z][a-z0-9]*)*)                  # camelCase (e.g., myVariable)
        # | ([A-Z][a-z0-9]*(?:[A-Z][a-z0-9]*)*)           # PascalCase (e.g., MyClass)
        # | ([a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*)              # snake_case (e.g., my_variable)
        # | ([a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*)              # Kebab-case (e.g., my-variable)

        # 8. Individual punctuation and bracketing characters
        # Includes standard and 'smart' quotes, and the asterisk '*'.
        | ([.,!?;:(){}\[\]<>"'`‘“'”*])

        # 9. Specific whitespace characters (newline, carriage return, tab, form feed) as tokens
        # These are now actual characters after unicode_escape.
        | ([\n\r\t\f])

        # 10. General whitespace (spaces)
        | (\s+) # Capture sequences of one or more spaces

        # 11. Any remaining sequence of non-whitespace characters (catch-all for symbols or other words)
        #| ([^\s]+)

        """, re.VERBOSE)

    return bool(token_pattern.match(aToken))

def _decode_text_if_needed(text: str) -> str:
    """
    Decodes the input string using unicode_escape if it contains potential
    escape sequences.
    """
    try:
        if '\\' in text:
            return text.encode('utf-8').decode('unicode_escape')
        else:
            return text
    except (UnicodeDecodeError, AttributeError):
        return text

def _tokenize_words_in_content(content: str) -> list[str]:
    """
    Helper function to tokenize words within extracted Markdown content.
    Applies rules for various casing conventions and zero-padded words.
    """
    word_regex = re.compile(r"""
        # Matches words containing letters, optionally numbers, then zero-padded digits,
        # then optionally more alphanumeric characters (e.g., test0023, ZeroPaddedWord00).
        [a-zA-Z]+[0-9]*0+\d+[a-zA-Z0-9]*
        |
        # camelCase (e.g., myVariable)
        [a-z]+(?:[A-Z][a-z0-9]*)*
        |
        # PascalCase (e.g., MyClass)
        [A-Z][a-z0-9]*(?:[A-Z][a-z0-9]*)*
        |
        # snake_case (e.g., my_variable)
        [a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*
        |
        # Kebab-case (e.g., my-variable)
        [a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*
        |
        # General alphanumeric words (catch-all for simple words)
        [a-zA-Z0-9]+
        """, re.VERBOSE)
    return [match.group(0) for match in word_regex.finditer(content)]

def piParseMarkdownElements(mdText: str) -> list[dict]:
    """
    Parses the input text to identify and extract details about Markdown elements.

    Args:
        mdText (str): The input string potentially containing Markdown.

    Returns:
        list: A list of dictionaries, where each dictionary describes a detected
              Markdown element with 'full_match', 'type', 'content', 'start', 'end'.
              'content' is the inner text of the Markdown element.
    """
    processed_mdText = _decode_text_if_needed(mdText)
    elements = []

    # Regex patterns for different Markdown elements and their content extraction.
    # The order is important: more specific patterns (like image links) before more general ones (like general links).
    # Capture groups are used to extract the content.
    # re.DOTALL allows '.' to match newlines for multi-line content.
    # re.MULTILINE allows '^' to match start of lines for block-level elements.
    markdown_element_patterns = [
        # Image links: ![alt text](url)
        (re.compile(r'(!\[(.*?)\]\(.*?\))', re.DOTALL), 'image_link'),
        # Standard links: [link text](url)
        (re.compile(r'(\[(.*?)\]\(.*?\))', re.DOTALL), 'link'),
        # Bold: **text**
        (re.compile(r'(\*\*(.*?)\*\*)', re.DOTALL), 'bold'),
        # Italic: *text* or _text_
        # Note: (?:...|...) ensures the whole match is one group, then inner groups are 2 or 3.
        (re.compile(r'(\*(.*?)\*|\_(.*?)\_)', re.DOTALL), 'italic'),
        # Strikethrough: ~~text~~
        (re.compile(r'(~~(.*?)~~)', re.DOTALL), 'strikethrough'),
        # Inline code: `code`
        (re.compile(r'(`([^`\n]*?)`)', re.DOTALL), 'inline_code'),
        # Superscript: X^2^
        (re.compile(r'([a-zA-Z0-9_]+\^(.+?)\^)', re.DOTALL), 'superscript'),
        # Headings: # Heading, ## Subheading, etc.
        (re.compile(r'(^\s*#{1,6}\s*(.*))', re.MULTILINE), 'heading'),
        # Blockquotes: > Quote
        (re.compile(r'(^\s*>\s*(.*))', re.MULTILINE), 'blockquote'),
        # Horizontal Rules (these don't have inner content, but we capture the full match)
        (re.compile(r'(^-{3,}$|^\*{3,}$|^_{3,}$)', re.MULTILINE), 'horizontal_rule')
    ]

    # To ensure we process non-overlapping matches and preserve order,
    # we find all matches and then sort them by their start position.
    all_matches_with_types = []
    for pattern_regex, element_type in markdown_element_patterns:
        for match in pattern_regex.finditer(processed_mdText):
            full_match_text = match.group(1) # The full Markdown element string

            # Determine content based on element type and regex groups
            content = ''
            if element_type == 'image_link' or element_type == 'link' or \
               element_type == 'bold' or element_type == 'strikethrough' or \
               element_type == 'inline_code' or element_type == 'superscript' or \
               element_type == 'heading' or element_type == 'blockquote':
                content = match.group(2) # Inner content is usually group 2
            elif element_type == 'italic':
                # Italic has two possible content groups depending on * or _
                content = match.group(2) or match.group(3)
            # Horizontal rules have no content, so content remains ''

            all_matches_with_types.append({
                'full_match': full_match_text,
                'type': element_type,
                'content': content.strip(), # Strip whitespace from content
                'start': match.start(1), # Start of the full match
                'end': match.end(1)      # End of the full match
            })

    # Sort matches by their starting position to process them in order
    all_matches_with_types.sort(key=lambda x: x['start'])

    # Filter out overlapping or nested matches, prioritizing earlier or longer matches.
    # This is a basic approach and might not handle all complex nesting scenarios perfectly.
    seen_ranges = []
    for m in all_matches_with_types:
        is_overlapping = False
        for s, e in seen_ranges:
            # If current match starts within a seen range, or overlaps
            if (m['start'] >= s and m['start'] < e) or \
               (m['end'] > s and m['end'] <= e) or \
               (m['start'] < s and m['end'] > e):
                is_overlapping = True
                break
        if not is_overlapping:
            elements.append(m)
            seen_ranges.append((m['start'], m['end']))

    return elements

def piMarkDownTokens(mdText: str) -> dict[str, list[str]]:
    """
    Extracts word tokens from the content of Markdown elements and maps them
    to their original full Markdown string. This is for review and modification.

    Args:
        mdText (str): The input string potentially containing Markdown.

    Returns:
        dict: A dictionary where keys are the full original Markdown element strings
              (e.g., "**bold text**") and values are lists of word tokens
              extracted from their inner content (e.g., ["bold", "text"]).
              Horizontal rules are excluded as they have no word content.
    """
    markdown_elements_data = piParseMarkdownElements(mdText)
    token_map = {}

    for element in markdown_elements_data:
        # Only process elements that have extractable content (not horizontal rules)
        if element['type'] != 'horizontal_rule':
            # Tokenize the inner content using the helper function
            inner_word_tokens = _tokenize_words_in_content(element['content'])
            # Map the original full Markdown string to its inner word tokens
            token_map[element['full_match']] = inner_word_tokens
    return token_map

def piReconstructMarkdown(original_text: str, modified_md_token_map: dict[str, list[str]]) -> str:
    """
    Reconstructs the original text, replacing the content of Markdown elements
    with potentially modified word tokens.

    Args:
        original_text (str): The original string before any modifications.
        modified_md_token_map (dict): A dictionary where keys are the full
                                     original Markdown element strings (e.g., "**old words**")
                                     and values are lists of the NEW word tokens
                                     (e.g., ["new", "words"]) for that element.

    Returns:
        str: The reconstructed string with modified Markdown elements.
    """
    processed_text = _decode_text_if_needed(original_text)
    markdown_elements_data = piParseMarkdownElements(processed_text)

    # Convert the string to a list of characters or segments for easier modification
    # This avoids issues with string immutability and re.sub overlapping.
    output_segments = []
    last_idx = 0

    for element in markdown_elements_data:
        original_full_match = element['full_match']
        element_type = element['type']

        # Append the text segment before the current Markdown element
        if element['start'] > last_idx:
            output_segments.append(processed_text[last_idx:element['start']])

        # Check if this Markdown element's content was modified
        if original_full_match in modified_md_token_map:
            # Reconstruct the inner content from the modified word tokens
            new_inner_content = " ".join(modified_md_token_map[original_full_match])

            # Re-wrap the new content with the correct Markdown syntax
            reconstructed_element = ""
            if element_type == 'bold':
                reconstructed_element = f"**{new_inner_content}**"
            elif element_type == 'italic':
                # This needs to be careful: if original was *italic*, preserve that.
                # If original was _italic_, preserve that.
                # A simple heuristic: check the original full match's delimiters.
                if original_full_match.startswith('**') or original_full_match.startswith('__'):
                    # This implies bold/strong, not just italic. Reconstruct as bold if it was.
                    reconstructed_element = f"**{new_inner_content}**"
                elif original_full_match.startswith('*'):
                    reconstructed_element = f"*{new_inner_content}*"
                elif original_full_match.startswith('_'):
                    reconstructed_element = f"_{new_inner_content}_"
                else: # Fallback, should not happen if parsing is correct
                    reconstructed_element = f"*{new_inner_content}*" # Default to '*'
            elif element_type == 'strikethrough':
                reconstructed_element = f"~~{new_inner_content}~~"
            elif element_type == 'inline_code':
                reconstructed_element = f"`{new_inner_content}`"
            elif element_type == 'superscript':
                # We need to find the base part from the original full match to reconstruct.
                # E.g., for "X^2^", if new_inner_content is "3", it should be "X^3^"
                base_match = re.match(r'([a-zA-Z0-9_]+)\^.*?\^', original_full_match)
                if base_match:
                    base_part = base_match.group(1)
                    reconstructed_element = f"{base_part}^{new_inner_content}^"
                else: # Fallback if base part couldn't be extracted, keep original structure
                    reconstructed_element = original_full_match.replace(element['content'], new_inner_content, 1)
            elif element_type == 'heading':
                # Reconstruct heading: preserve leading spaces and hash count
                hash_match = re.match(r'^\s*(#{1,6})\s*', original_full_match, re.MULTILINE)
                if hash_match:
                    hashes = hash_match.group(1)
                    reconstructed_element = f"{hashes} {new_inner_content}"
                else: # Fallback
                    reconstructed_element = new_inner_content # Should not happen
            elif element_type == 'blockquote':
                # Reconstruct blockquote: preserve leading spaces and '>'
                blockquote_match = re.match(r'^\s*(>)\s*', original_full_match, re.MULTILINE)
                if blockquote_match:
                    gt_char = blockquote_match.group(1)
                    reconstructed_element = f"{gt_char} {new_inner_content}"
                else: # Fallback
                    reconstructed_element = new_inner_content # Should not happen
            elif element_type == 'link':
                # Reconstruct link: [new content](original url)
                url_match = re.search(r'\]\((.*?)\)', original_full_match)
                if url_match:
                    url = url_match.group(1)
                    reconstructed_element = f"[{new_inner_content}]({url})"
                else: # Fallback
                    reconstructed_element = original_full_match.replace(element['content'], new_inner_content, 1)
            elif element_type == 'image_link':
                # Reconstruct image link: ![new alt text](original url)
                url_match = re.search(r'\]\((.*?)\)', original_full_match)
                if url_match:
                    url = url_match.group(1)
                    reconstructed_element = f"![{new_inner_content}]({url})"
                else: # Fallback
                    reconstructed_element = original_full_match.replace(element['content'], new_inner_content, 1)
            elif element_type == 'horizontal_rule':
                reconstructed_element = original_full_match # No content to change for HR
            else:
                # If type is unknown or no specific reconstruction logic,
                # just replace the inner content within the original full match
                reconstructed_element = original_full_match.replace(element['content'], new_inner_content, 1)

            output_segments.append(reconstructed_element)
        else:
            # If the element was not in the modified_md_token_map, keep it as is
            output_segments.append(original_full_match)

        last_idx = element['end']

    # Append any remaining text after the last Markdown element
    if last_idx < len(processed_text):
        output_segments.append(processed_text[last_idx:])

    return "".join(output_segments)

