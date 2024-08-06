import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

def test():
    
    print('\033[31m' + 'some red text')
    print('\033[39m')  # and reset to default color
    print()
    print(f"{Fore.RED}C{Fore.GREEN}O{Fore.YELLOW}L{Fore.BLUE}O{Fore.MAGENTA}R{Fore.CYAN}S{Fore.WHITE}!")
    print(f"{Fore.RED}Red Text")
    print(f"{Fore.GREEN}Green Text")
    print(f"{Fore.YELLOW}Yellow Text")
    print(f"{Fore.BLUE}Blue Text")
    print(f"{Fore.MAGENTA}Magenta Text")
    print(f"{Fore.CYAN}Cyan Text")
    print(f"{Fore.WHITE}White Text")
    print()
    print(f"{Back.RED}B{Back.GREEN}A{Back.YELLOW}C{Back.BLUE}K{Back.MAGENTA}G{Back.CYAN}R{Back.WHITE}O{Back.RED}U{Back.GREEN}N{Back.YELLOW}D{Back.BLUE}!")
    print(f"{Back.RED}Red Background")
    print(f"{Back.GREEN}Green Background")
    print(f"{Back.YELLOW}Yellow Background")
    print(f"{Back.BLUE}Blue Background")
    print(f"{Back.MAGENTA}Magenta Background")
    print(f"{Back.CYAN}Cyan Background")
    print(f"{Back.WHITE}White Background")
    print()
    print(f"{Style.DIM}S{Style.NORMAL}T{Style.BRIGHT}Y{Style.DIM}L{Style.NORMAL}E{Style.BRIGHT}!")
    print(f"{Style.DIM}Dim Text")
    print(f"{Style.NORMAL}Normal Text")
    print(f"{Style.BRIGHT}Bright Text")
    print()
    print(f"{Fore.YELLOW}{Back.RED}C{Back.GREEN}{Fore.RED}O{Back.YELLOW}{Fore.BLUE}M{Back.BLUE}{Fore.BLACK}B{Back.MAGENTA}{Fore.CYAN}I{Back.CYAN}{Fore.GREEN}N{Back.WHITE}A{Back.RED}T{Back.GREEN}I{Back.YELLOW}O{Back.BLUE}N")
    print(f"{Fore.GREEN}{Back.YELLOW}{Style.BRIGHT}Green Text - Yellow Background - Bright")
    print(f"{Fore.CYAN}{Back.WHITE}{Style.DIM}Cyan Text - White Background - Dim")


'''
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
'''
